import streamlit as st
import stripe

class StripeHandler:
    def __init__(self):
        stripe.api_key = st.secrets["stripe_secret_key"]
    
    def create_checkout_session(self, user_email: str, credits: int, price: int):
        """
        Create Stripe checkout session (TEST MODE ONLY)
        price: in cents (e.g., 1000 = $10.00)
        """
        try:
            # In production, you would create or retrieve a Stripe Customer
            # For demo, we just use the email
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'{credits} ArchNet Credits',
                        },
                        'unit_amount': price,  # in cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url='https://archnet-demo.streamlit.app//?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='https://archnet-demo.streamlit.app//?cancelled=true',
                metadata={
                    'user_email': user_email,
                    'credits': credits
                }
            )
            return session.url
        except Exception as e:
            st.error(f"Stripe error: {e}")
            return None
    
    def get_credit_packages(self):
        """Define available credit packages"""
        return [
            {"credits": 10, "price": 490, "label": "10 Credits - $4.90"},
            {"credits": 25, "price": 990, "label": "25 Credits - $9.90"},
            {"credits": 100, "price": 2990, "label": "100 Credits - $29.90"},
        ]
