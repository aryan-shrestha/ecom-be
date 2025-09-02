import datetime
import requests
import json

from django.views import View
from django.shortcuts import redirect
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from cart.models import Cart

from .models import Order, Payment
from .utils import move_cart_items_to_ordered_items
from .serializers import OrderSerializer

# Create your views here.


def get_session_id(request):
    session_id = request.session.session_key
    if session_id == None:
        request.session.save()
        session_id = request.session.session_key

    return session_id


class InitiateKhaltiPayment(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]
    queryset = Order.objects.all()
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        session_key = get_session_id(request)
        order = Order()
        order.session_key = session_key
        order.first_name = request.data.get('first_name')
        order.last_name = request.data.get('last_name')
        order.phone_no = request.data.get('phone_no')
        order.email = request.data.get('email')
        order.address_line_1 = request.data.get('address_line_1')
        order.address_line_2 = request.data.get('address_line_2')
        order.order_note = request.data.get('order_note')
        order.grand_total = request.data.get('grand_total')
        order.vat = request.data.get('vat')
        order.save()

        # generate order number
        yr = int(datetime.date.today().strftime('%Y'))
        dt = int(datetime.date.today().strftime('%d'))
        mt = int(datetime.date.today().strftime('%m'))
        d = datetime.date(yr, mt, dt)
        current_date = d.strftime('%Y%m%d')  # 20230626
        order_number = current_date + str(order.id)
        order.order_number = order_number
        order.save()

        # khalti payment initialization

        url = "https://a.khalti.com/api/v2/epayment/initiate/"
        return_url = request.build_absolute_uri(
            '/orders/verify-khalti-payment/')
        purchase_order_id = order.order_number
        amount = float(order.grand_total) * 100
        customer_name = f"{order.first_name} {order.last_name}"
        payload = json.dumps({
            "return_url": return_url,
            "website_url": "http://localhost:5173/",
            "amount": int(amount),
            "purchase_order_id": purchase_order_id,
            "purchase_order_name": customer_name,
            "customer_info": {
                "name": customer_name,
                "email": order.email,
                "phone": order.phone_no
            }
        })

        headers = {
            'Authorization': 'key 12a48698337847ada2f729e872f04867',
            'Content-Type': 'application/json',
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        print(response.text)
        new_res = json.loads(response.text)
        print(new_res)
        return Response({'payment_url': new_res['payment_url']}, status=status.HTTP_200_OK)


class VerifyKhaltiPayment(View):

    def get(self, request, format=None):
        pidx = request.GET.get('pidx')

        headers = {
            'Authorization': 'key 12a48698337847ada2f729e872f04867',
            'Content-Type': 'application/json',
        }

        payload = json.dumps({
            'pidx': pidx
        })
        url = "https://a.khalti.com/api/v2/epayment/lookup/"
        response = requests.request("POST", url, headers=headers, data=payload)
        response = json.loads(response.text)

        if response['status'] == 'Completed':
            amount = float(request.GET.get('amount'))/100
            order_number = request.GET.get('purchase_order_id')
            payment_id = request.GET.get('pidx')
            trasaction_id = request.GET.get('trasaction_id')

            try:
                order = Order.objects.get(order_number=order_number)
            except Order.DoesNotExist:
                return Response({'detail': "Order does not exists"}, status=status.HTTP_404_NOT_FOUND)
            except:
                return Response({"detail": "Something went wrong"}, status=status.HTTP_400_BAD_REQUEST)

            payment = Payment(
                session_key=order.session_key,
                payment_id=payment_id,
                amount_paid=amount,
                payment_method="Khalti",
                status="complete"
            )
            payment.save()
            order.status = "Confirmed"
            order.payment = payment
            order.is_ordered = True
            order.save()

            cart = Cart.objects.get(session_key=order.session_key)
            cart_items = cart.items.all()

            move_cart_items_to_ordered_items(
                request, order, payment, cart_items)

            response = redirect(
                "https://the-scarlett-cloud.vercel.app/payment-success")
            response['Cache-Control'] = 'no-store'
            return response

        else:
            response = redirect(
                "https://the-scarlett-cloud.vercel.app/payment-failure")
            response['Cache-Control'] = 'no-store'
            return response


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        session_key = get_session_id(self.request)
        queryset = Order.objects.filter(
            session_key=session_key).order_by('-created_at')

        if queryset.exists():
            return queryset.first()
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        order_serializer = self.get_serializer(instance)
        return Response(order_serializer.data, status=status.HTTP_200_OK)


class OrderListView(generics.ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]
