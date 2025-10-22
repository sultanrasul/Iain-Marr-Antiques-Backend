"""
This call sends a message to one recipient.
"""
from mailjet_rest import Client
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

def send_email(selected_products, customer, emailAddress):

  api_key = os.environ['MAILJET_API_KEY']
  api_secret = os.environ['MAILJET_SECRET_KEY']
  mailjet = Client(auth=(api_key, api_secret), version='v3.1')
  data = {
    'Messages': [
          {
              "From": {
                  "Email": "sales@iainmarrantiques.store",
                  "Name": "Iain Marr Antiques"
              },
              "To": [
                  {
                      "Email": emailAddress,
                      "Name": customer
                  }
              ],
              "Subject": "Your Receipt from Iain Marr Antiques",
              "TextPart": "Dear passenger 1, welcome to Mailjet! May the delivery force be with you!",
              "HTMLPart": construct_email(selected_products, customer)

          }
      ]
  }
  result = mailjet.send.create(data=data)
  print(result.status_code)
  print(result.json())


def construct_email(selected_products, customer):
    # Prepare items HTML dynamically
    items_html = ""
    subtotal = 0
    max_digits = len(str(len(selected_products)))
    
    for i, product in enumerate(selected_products, 1):
        name = product.get("name", "Unknown Item")
        price = product.get("price", 0)
        subtotal += price
        formatted_num = f"IMA{i:<{max_digits}}"

        # Apply background color for even rows
        bg_color = ' style="background-color:#f8fafc;"' if i % 2 == 0 else ''
        
        items_html += f"""
          <tr{bg_color}>
            <td valign="top" style="padding:8px; width:50px; font-size:15px; vertical-align:top; white-space:nowrap;">{formatted_num} -</td>
            <td valign="top" style="padding:8px 8px 8px 0px; font-size:15px; vertical-align:top; word-break:break-word; line-height:1.5;">{name}</td>
            <td valign="top" style="padding:8px; width:80px; font-size:15px; text-align:right; vertical-align:top; white-space:nowrap;">£{price:,.2f}</td>
          </tr>
        """
    
    total = subtotal
    date_today = datetime.now().strftime("%d.%m.%Y")

    # Conditionally render greeting and "Sold To"
    greeting_html = f"""
        <p>Dear <span style="color:#011993; font-weight:bold;">{customer}</span>,</p>
    """ if customer else ""

    sold_to_html = f"""
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="font-family:'Palatino Linotype', 'Book Antiqua', 'Times New Roman', serif;">
          <tr>
            <td style="font-weight:bold; text-align:left;">Sold To: <span style="font-weight:normal;">{customer}</span></td>
            <td style="text-align:right;"><strong>Date:</strong> {date_today}</td>
          </tr>
        </table>
    """ if customer else f"""
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="font-family:'Palatino Linotype', 'Book Antiqua', 'Times New Roman', serif;">
          <tr>
            <td style="text-align:right;"><strong>Date:</strong> {date_today}</td>
          </tr>
        </table>
    """

    html = f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>Iain Marr Antiques - Purchase Receipt</title>
  </head>
  <body style="margin:0; padding:0; background-color:#f8fafc; font-family:Georgia, 'Times New Roman', serif; color:#333333;">
    <center>

      <!-- HEADER -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:40px;">
        <tr>
          <td align="center" style="padding-bottom:35px;padding-top:35px;">
            <img src="https://iain-marr-antiques-frontend.pages.dev/email_logo.png" alt="Iain Marr Antiques" width="550" style="max-width:100%; height:auto; display:block;">
          </td>
        </tr>
        <tr>
          <td align="center" style="color:#011993; font-size:14px; letter-spacing:0.4px; text-transform:uppercase; line-height:1.4;">
            Member of L.A.P.A.D.A and The Silver Society.<br>
            Dealers in Fine Silver, Scottish Regalia,<br>
            Jewellery and Ceramics
            <br><br>
            2 Aird House, High Street, Beauly, Scotland, IV4 7BS.
            <br>
            <a href="tel:+441463782372" style="color:#011993; text-decoration:none;">Tel: 01463 782372</a> &nbsp; | &nbsp;
            <a href="mailto:info@iain-marr-antiques.com" style="color:#011993; text-decoration:none;">info@iain-marr-antiques.com</a>
            <br>
            <a href="https://www.iain-marr-antiques.com" style="color:#011993; text-decoration:none;">www.iain-marr-antiques.com</a>
          </td>
        </tr>
      </table>

      <!-- MESSAGE -->
      <table width="90%" cellpadding="0" cellspacing="0" border="0" style="max-width:650px; margin-top:40px; background-color:#ffffff; border:1px solid #d1d5db; border-radius:8px; box-shadow:0 4px 12px rgba(1,25,147,0.08);">
        <tr>
          <td style="padding:20px 25px; text-align:left; font-size:15px; line-height:1.5;">
            {greeting_html}
            <p>
              Thank you for choosing <span style="color:#011993; font-weight:bold;">Iain Marr Antiques</span> for your recent purchase. 
              We're delighted you've found a piece that speaks to you, and we hope it brings you joy for years to come.
            </p>
            <p>Please see below for details of your purchase.</p>
            <p>Kind regards,<br>
              <span style="color:#011993; font-weight:bold;">Iain Marr Antiques</span>
            </p>
          </td>
        </tr>
      </table>

      <!-- ORDER DETAILS -->
      <table width="90%" cellpadding="0" cellspacing="0" border="0" style="max-width:650px; margin-top:25px; background-color:#ffffff; border:1px solid #d1d5db; border-radius:8px;">
        <tr>
          <td style="padding:20px 25px; font-size:15px;">
            <!-- SOLD TO + DATE -->
            {sold_to_html}

            <hr style="border:none; border-top:1px solid #e5e7eb; margin:10px 0;">

            <!-- ITEMS -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse; font-family:'Palatino Linotype', 'Book Antiqua', 'Times New Roman', serif;">
              {items_html}
            </table>

            <hr style="border:none; border-top:1px solid #e5e7eb; margin:10px 0;">

            <!-- Totals -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="font-family:'Palatino Linotype', 'Book Antiqua', 'Times New Roman', serif;">
              <tr>
                <td style="padding:6px 4px; font-size:15px;">Subtotal:</td>
                <td style="padding:6px 4px; font-size:15px; text-align:right;">£{subtotal:,.2f}</td>
              </tr>
              <tr>
                <td style="padding:6px 4px; font-size:15px;">Total:</td>
                <td style="padding:6px 4px; font-size:15px; text-align:right;">£{total:,.2f}</td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <!-- FOOTER -->
      <table width="90%" cellpadding="0" cellspacing="0" border="0" style="max-width:650px; margin-top:25px;">
        <tr>
          <td align="center" style="font-size:12px; color:#64748b; line-height:1.4; padding-bottom:40px;">
            <p style="margin:5px 0;">VAT Reg No. 2965 743 08 | VAT has not been charged on the above items</p>
            <p style="margin:5px 0;">&copy; {datetime.now().year} Iain Marr Antiques | All rights reserved</p>
          </td>
        </tr>
      </table>

    </center>
  </body>
</html>
"""
    return html
