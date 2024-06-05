from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import UserPayment
from .email import notify_user
import stripe
import time
import os


stripe.api_key = settings.STRIPE_SECRET_KEY_TEST


@login_required(login_url='login')
def product_page(request):
    '''Stripe product page for user's checkout'''
    if request.method == 'POST':
        price_lookup_key = request.POST['price_lookup_key']
        prices = stripe.Price.list(lookup_keys=[price_lookup_key], expand=['data.product'])
        print(prices)
        price_item = prices.data[0]
        checkout_session = stripe.checkout.Session.create(
            payment_method_types = ['card'],
            line_items = [
                {
                    'price': price_item.id,
                    'quantity': 1,
                },
            ],
            mode = 'payment',
            customer_creation = 'always',
            success_url = settings.REDIRECT_DOMAIN + '/payment_successful?session_id={CHECKOUT_SESSION_ID}',
            cancel_url = settings.REDIRECT_DOMAIN + '/payment_cancelled',
        )
        return redirect(checkout_session.url, code=303)
    return render(request, 'payment/product_page.html')
    

def payment_successful(request):
    checkout_session_id = request.GET.get('session_id', None)
    session = stripe.checkout.Session.retrieve(checkout_session_id)
    customer = stripe.Customer.retrieve(session.customer)
    user_id = request.user.user_id
    print(user_id)
    user_payment = UserPayment.objects.get(app_user=user_id)
    user_payment.stripe_checkout_id = checkout_session_id
    user_payment.save()
    notify_user(request.user.email, "Payment Is Successful.")
    return render(request, 'payment/payment_successful.html', {'customer': customer})


def payment_cancelled(request):
    notify_user(request.user.email, "Payment Was Cancelled.")
    return render(request, 'payment/payment_cancelled.html')

@csrf_exempt
def stripe_webhook(request):
    time.sleep(10)
    payload = request.body
    signature_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, signature_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        session_id = session.get('id', None)
        time.sleep(15)
        user_payment = UserPayment.objects.get(stripe_checkout_id=session_id)
        line_items = stripe.checkout.Session.list_line_items(session_id, limit=1)
        user_payment.is_payed = True
        user_payment.save()

    return HttpResponse(status=200)