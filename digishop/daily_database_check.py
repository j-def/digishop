from paypalrestsdk import Sale, Payment
import paypalrestsdk
import datetime
import pyodbc
from data_manager import manager
from digishop_emailer import emailer
dbserver = 'REGCONSERVER1'
dbdatabase = 'digishop'
dbusername = 'belotecainventory'
dbpassword = 'belotecainventory'
import math
cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
cursor = cnxn.cursor()
e = emailer()
def check_listing(owner, listingId):
    cursor.execute(
        "SELECT withdraw_account, moment_id, distinct_moment_id, serial, price, paypal_transaction, status, sold_timestamp, buyer_username  FROM sold_listings WHERE owner_username=? AND listing_id=?",
        (owner, listingId))
    withdraw_account, moment_id, distinct_moment_id, serial, price, paypal_transaction, status, sold_timestamp, buyer = cursor.fetchone()
    if status == "awaiting_moment":
        if manager().check_user_for_moment_by_id_specific(withdraw_account,
                                                          distinct_moment_id + ":" + serial + "/" + str(
                                                              manager().grab_moment_by_id(moment_id)[
                                                                  'circulationCount'])):
            cursor.execute("UPDATE sold_listings SET status='sent' WHERE owner_username=? AND listing_id=?",
                           (owner, listingId))
            cursor.execute("UPDATE users SET wallet_balance=convert (float, wallet_balance)+? WHERE username=?",
                           (float((float(price) * 0.92) - 0.3)), owner)
            cnxn.commit()
            cnxn.close()
            e.sale_completed(buyer, owner, listingId)
            return
        elif (7 - math.floor((int(datetime.datetime.now().timestamp()) - int(sold_timestamp)) / 86400)) < 0:
            try:
                cursor.execute("UPDATE sold_listings SET status='cancelled' WHERE owner_username=? AND listing_id=?",
                               (owner, listingId))
                cnxn.commit()
                e.sale_cancelled(buyer, owner, listingId)
                paypalrestsdk.configure({
                    'mode': 'live',  # sandbox or live
                    'client_id': 'ATusgTPA59uRaBrfFRy1JVtNSt5O7FBkkF1wMEwU-XyKkixH3CwIKRqrR9yb2UEckX9NkjVKY4ydlgUf',
                    'client_secret': 'ECQS0iOl1Vyfc5ZZm_gn4TRcXXKqYAXdxDyvK4Zf3w3wXc4Fkt45Rx5M9DOhEnbI2Y5cDVZEMRbAW1Z9'})
                payment = Payment.find("PAYID-MBTL4ZI8CY35417XW0892443")
                sale = Sale.find(payment['transactions'][0]['related_resources'][0]['sale']['id'])
                print(sale)
                print(sale['amount']['details']['subtotal'])

                refund = sale.refund({
                    "amount": {
                        "total": sale['amount']['details']['subtotal'],
                        "currency": "USD"},
                "description": "Seller Failed to Send Item"})

                # Check refund status
                if refund.success():
                    print("Refund[%s] Success" % (refund.id))
                    return
                else:
                    cursor.execute("UPDATE sold_listings SET status='cancelled_error' WHERE owner_username=? AND listing_id=?",
                                   (owner, listingId))
                    cnxn.commit()
                    print("Unable to Refund")
                    print(refund.error)
                    return
            except:
                cursor.execute(
                    "UPDATE sold_listings SET status='cancelled_error' WHERE owner_username=? AND listing_id=?",
                    (owner, listingId))
                cnxn.commit()

        else:
            e.moment_send_notice(owner, listingId)
            return
    else:
        cnxn.close()
        return


cursor.execute("SELECT owner_username, listing_id FROM sold_listings WHERE status='awaiting_moment'")
for item in cursor.fetchall():
    check_listing(item[0], item[1])