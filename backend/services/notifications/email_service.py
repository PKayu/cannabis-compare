"""Email notification service using SendGrid"""
import os
from typing import Optional
from models import User, Product, Price, Dispensary


class EmailNotificationService:
    """Send email notifications for alerts using SendGrid"""

    @staticmethod
    def send_stock_alert(user: User, product: Product, price: Price, dispensary: Dispensary) -> bool:
        """
        Send email when product comes back in stock

        Args:
            user: User to notify
            product: Product that's back in stock
            price: Price record with current price
            dispensary: Dispensary where product is available

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
            sender_email = os.getenv("NOTIFICATION_EMAIL_SENDER", "alerts@utahbud.com")

            if not sendgrid_api_key:
                print("Warning: SENDGRID_API_KEY not configured, skipping email")
                return False

            subject = f"🎉 {product.name} is back in stock!"

            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2d5016;">{product.name} is now available!</h2>
                    <p><strong>Dispensary:</strong> {dispensary.name}</p>
                    <p><strong>Price:</strong> ${price.amount:.2f}</p>
                    <p><strong>Product Type:</strong> {product.product_type}</p>
                    <p style="margin-top: 30px;">
                        <a href="https://utahbud.com/products/{product.id}"
                           style="background-color: #2d5016; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">
                            View Product
                        </a>
                    </p>
                    <p style="color: #666; font-size: 12px; margin-top: 40px;">
                        You're receiving this because you added {product.name} to your watchlist.
                        <br>
                        <a href="https://utahbud.com/watchlist">Manage your watchlist</a>
                    </p>
                </body>
            </html>
            """

            message = Mail(
                from_email=sender_email,
                to_emails=user.email,
                subject=subject,
                html_content=html_content
            )

            sg = SendGridAPIClient(sendgrid_api_key)
            response = sg.send(message)

            return response.status_code in [200, 201, 202]

        except Exception as e:
            print(f"Failed to send stock alert email: {e}")
            return False

    @staticmethod
    def send_price_drop_alert(
        user: User,
        product: Product,
        price: Price,
        dispensary: Dispensary,
        percent_change: float
    ) -> bool:
        """
        Send email when price drops

        Args:
            user: User to notify
            product: Product with price drop
            price: Price record with new price
            dispensary: Dispensary with the price drop
            percent_change: Percentage change (negative number)

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
            sender_email = os.getenv("NOTIFICATION_EMAIL_SENDER", "alerts@utahbud.com")

            if not sendgrid_api_key:
                print("Warning: SENDGRID_API_KEY not configured, skipping email")
                return False

            discount_display = abs(percent_change)
            old_price = price.previous_price if price.previous_price else price.amount

            subject = f"💰 {discount_display:.0f}% price drop on {product.name}"

            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2d5016;">Price drop alert!</h2>
                    <h3>{product.name}</h3>
                    <div style="background-color: #f0f8f0; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <p style="font-size: 24px; margin: 0;">
                            <span style="text-decoration: line-through; color: #999;">${old_price:.2f}</span>
                            <strong style="color: #2d5016; margin-left: 10px;">${price.amount:.2f}</strong>
                        </p>
                        <p style="color: #2d5016; font-size: 18px; margin: 10px 0 0 0;">
                            Save {discount_display:.0f}%!
                        </p>
                    </div>
                    <p><strong>Dispensary:</strong> {dispensary.name}</p>
                    <p><strong>Product Type:</strong> {product.product_type}</p>
                    <p style="margin-top: 30px;">
                        <a href="https://utahbud.com/products/{product.id}"
                           style="background-color: #2d5016; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">
                            View Product
                        </a>
                    </p>
                    <p style="color: #666; font-size: 12px; margin-top: 40px;">
                        You're receiving this because you're watching {product.name} for price drops.
                        <br>
                        <a href="https://utahbud.com/watchlist">Manage your watchlist</a>
                    </p>
                </body>
            </html>
            """

            message = Mail(
                from_email=sender_email,
                to_emails=user.email,
                subject=subject,
                html_content=html_content
            )

            sg = SendGridAPIClient(sendgrid_api_key)
            response = sg.send(message)

            return response.status_code in [200, 201, 202]

        except Exception as e:
            print(f"Failed to send price drop alert email: {e}")
            return False
