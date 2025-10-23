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
    # Build the dynamic product rows
    items_html = ""
    subtotal = 0

    for i, product in enumerate(selected_products, 1):
        name = product.get("name", "Unknown Item")
        id = product.get("id", f"IMA{i}")
        price = product.get("price", 0)
        subtotal += price

        # Apply alternate background for even rows
        bg_color = ' style="background-color:#f8fafc;"' if i % 2 == 0 else ''

        items_html += f"""
          <tr{bg_color}>
            <td class="item-code" valign="top" style="padding:8px; width:50px; font-size:15px; vertical-align:top; white-space:nowrap;">{id} -</td>
            <td class="item-desc" valign="top" style="padding:8px 8px 8px 0px; font-size:15px; vertical-align:top; word-break:break-word; line-height:1.6;">{name}</td>
            <td class="item-price" valign="top" style="padding:8px; width:80px; font-size:15px; text-align:right; vertical-align:top; white-space:nowrap;">£{price:,.2f}</td>
          </tr>
        """

    total = subtotal
    date_today = datetime.now().strftime("%d.%m.%Y")

    # Optional customer details
    customer_html = (
        f'<span style="color:#011993; font-weight:bold;">{customer}</span>'
        if customer else "Valued Customer"
    )

    sold_to_html = (
        f"<span style='font-weight:normal;'>{customer}</span>"
        if customer else "Online Purchase"
    )

    html = f"""\
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>Iain Marr Antiques - Purchase Receipt</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
      td.content p {{
        margin: 0 0 14px 0 !important;
        line-height: 1.8 !important;
      }}
      .item-code {{
        vertical-align: top !important;
        padding-top: 10px !important;
        font-weight: bold;
      }}
      .item-desc {{
        line-height: 1.65 !important;
        padding-top: 7px !important;
      }}
      @media only screen and (max-width: 400px) {{
        .items-table,
        .items-table tr,
        .items-table td {{
          display: block !important;
          width: 100% !important;
          box-sizing: border-box;
        }}
        .item-code {{
          display: inline-block !important;
          width: auto !important;
          margin-bottom: 4px;
          padding-left: 4px !important;
        }}
        .item-desc {{
          padding-left: 4px !important;
          font-size: 15px !important;
          line-height: 1.6 !important;
        }}
        .item-price {{
          text-align: right !important;
          padding-top: 6px !important;
          border-top: 1px dashed #e5e7eb !important;
          margin-top: 6px !important;
        }}
        table.container {{
          width: 100% !important;
          max-width: 100% !important;
        }}
        td.content {{
          padding: 18px 16px !important;
        }}
      }}
    </style>
  </head>
  <body style="margin:0; padding:0; background-color:#EDF5FF; font-family:Georgia, 'Times New Roman', serif; color:#333333;">
    <center>
      <!-- HEADER -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:40px;">
        <tr>
          <td align="center" style="padding-bottom:35px; padding-top:35px;">
            <img class="logo" src="https://iain-marr-antiques-frontend.pages.dev/email_logo.png" alt="Iain Marr Antiques" width="550" style="max-width:100%; height:auto; display:block;">
          </td>
        </tr>
        <tr>
          <td align="center" style="color:#011993; font-size:14px; letter-spacing:0.4px; text-transform:uppercase; line-height:1.4;">
            Member of L.A.P.A.D.A and The Silver Society.<br>
            Dealers in Fine Silver, Scottish Regalia,<br>
            Jewellery and Ceramics
            <br><br>
            2 Aird House, High Street, Beauly, Scotland, IV4 7BS.<br>
            <a href="tel:+441463782372" style="color:#011993; text-decoration:none;">Tel: 01463 782372</a> &nbsp; | &nbsp;
            <a href="mailto:info@iain-marr-antiques.com" style="color:#011993; text-decoration:none;">info@iain-marr-antiques.com</a><br>
            <a href="https://www.iain-marr-antiques.com" style="color:#011993; text-decoration:none;">www.iain-marr-antiques.com</a>
          </td>
        </tr>
      </table>

      <!-- MESSAGE -->
      <table class="container" width="90%" cellpadding="0" cellspacing="0" border="0" style="max-width:650px; margin-top:40px; background-color:#ffffff; border:1px solid #d1d5db; border-radius:8px; box-shadow:0 4px 12px rgba(1,25,147,0.08);">
        <tr>
          <td class="content" style="padding:20px 25px; text-align:left; font-size:15px; line-height:1.6;">
            <p>Dear {customer_html},</p>
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
      <table class="container" width="90%" cellpadding="0" cellspacing="0" border="0" style="max-width:650px; margin-top:25px; background-color:#ffffff; border:1px solid #d1d5db; border-radius:8px;">
        <tr>
          <td class="content" style="padding:20px 25px; font-size:15px;">
            <!-- SOLD TO + DATE -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="font-weight:bold; text-align:left;">Sold To: {sold_to_html}</td>
                <td style="text-align:right;"><strong>Date:</strong> {date_today}</td>
              </tr>
            </table>

            <hr style="border:none; border-top:1px solid #e5e7eb; margin:10px 0;">

            <!-- ITEMS TABLE -->
            <table class="items-table" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse; font-family:'Palatino Linotype','Book Antiqua','Times New Roman',serif;">
              {items_html}
            </table>

            <hr style="border:none; border-top:1px solid #e5e7eb; margin:10px 0;">

            <!-- Totals -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="font-family:'Palatino Linotype','Book Antiqua','Times New Roman',serif;">
              <tr>
                <td style="padding:6px 4px; font-size:16px;">Subtotal:</td>
                <td style="padding:6px 4px; font-size:16px; text-align:right;">£{subtotal:,.2f}</td>
              </tr>
              <tr>
                <td style="padding:6px 4px; font-size:16px;">Total:</td>
                <td style="padding:6px 4px; font-size:16px; text-align:right;">£{total:,.2f}</td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <!-- FOOTER -->
      <table class="container" width="90%" cellpadding="0" cellspacing="0" border="0" style="max-width:650px; margin-top:25px;">
        <tr>
          <td align="center" style="font-size:12px; color:#64748b; line-height:1.4; padding-bottom:40px;">
            <p style="margin:5px 0;">VAT Reg No. 2965 743 08 | VAT has not been charged on the above items</p>
            <p style="margin:5px 0;">&copy; {datetime.now().year} Iain Marr Antiques | All rights reserved</p>
          </td>
        </tr>
      </table>
    </center>
  </body>
</html>"""

    return html



