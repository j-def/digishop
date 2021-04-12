import datetime
import pyodbc
import sendgrid
from data_manager import manager
import math
dbserver = 'REGCONSERVER1'
dbdatabase = 'digishop'
dbusername = 'belotecainventory'
dbpassword = 'belotecainventory'

class emailer:
    def __init__(self):
        self.cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        self.cursor = self.cnxn.cursor()

    def __get_email(self, user):
        self.cursor.execute("SELECT email from users WHERE username=?", (user))
        try:
            return self.cursor.fetchone()[0]
        except:
            return

    def sale_creation(self, buyer, seller, order_id):
        sg = sendgrid.SendGridAPIClient(api_key="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")
        TEMPLATE_ID = "d-806f4f57f9be4502a2a1289d57c5e267"
        FROM_EMAIL = "DigiShop<donotreply@digishop.gg>"
        TO_EMAILS = [(self.__get_email(buyer))]
        message = sendgrid.Mail(
            from_email=FROM_EMAIL,
            to_emails=TO_EMAILS)

        self.cursor.execute("SELECT price, withdraw_account, sold_timestamp, moment_id, serial from sold_listings WHERE order_id = ?", (order_id))
        price, withdraw_account, sold_timestamp, moment_id, momentSerial = self.cursor.fetchone()
        momentData = manager().grab_moment_by_id(moment_id)
        # pass custom values for our HTML placeholders
        message.dynamic_template_data = {
            'orderId': order_id,
            'price': str(price),
            'shipAccount': str(withdraw_account),
            'date': datetime.datetime.fromtimestamp(int(sold_timestamp)).strftime("%m-%d-%Y %H:%M"),
            'name': momentData['play']['stats']['playerName'],
            'serial': str(momentSerial) + "/" + str(momentData['circulationCount']),
            'type': momentData['play']['stats']['playCategory'],
            'set': momentData['set']['flowName'],
            'momentDate': datetime.datetime.fromisoformat(momentData['play']['stats']['dateOfMoment'][:-1]).strftime(
                '%m-%d-%Y'),
            'series': "Series " + str(momentData['set']['flowSeriesNumber']),
            'momentIcon': manager().grab_moment_icon_by_id(moment_id),
            'receieveBy': str(datetime.datetime.fromtimestamp(int(sold_timestamp)+604800).strftime("%m-%d-%Y"))
        }
        message.template_id = TEMPLATE_ID
        sg.send(message)

        TEMPLATE_ID = "d-3c4328220e6a423b9da5352f46f2b2d6"
        FROM_EMAIL = "DigiShop<donotreply@digishop.gg>"
        TO_EMAILS = [(self.__get_email(seller))]
        message = sendgrid.Mail(
            from_email=FROM_EMAIL,
            to_emails=TO_EMAILS)

        message.dynamic_template_data = {
            'orderId': order_id,
            'price': str(price),
            'shipAccount': str(withdraw_account),
            'date': datetime.datetime.fromtimestamp(int(sold_timestamp)).strftime("%m-%d-%Y %H:%M"),
            'name': momentData['play']['stats']['playerName'],
            'serial': str(momentSerial) + "/" + str(momentData['circulationCount']),
            'type': momentData['play']['stats']['playCategory'],
            'set': momentData['set']['flowName'],
            'momentDate': datetime.datetime.fromisoformat(momentData['play']['stats']['dateOfMoment'][:-1]).strftime(
                '%m-%d-%Y'),
            'series': "Series " + str(momentData['set']['flowSeriesNumber']),
            'momentIcon': manager().grab_moment_icon_by_id(moment_id),
            'pendingBalance': str(round(((float(price) * 0.92) - 0.30), 2)),
            'sendEndDate': str(datetime.datetime.fromtimestamp(int(sold_timestamp) + 604800).strftime("%m-%d-%Y"))
        }

        message.template_id = TEMPLATE_ID
        sg.send(message)

    def sale_cancelled(self, buyer, seller, order_id):
        sg = sendgrid.SendGridAPIClient(api_key="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")
        TEMPLATE_ID = "d-639d1bffc18d4bb6a58adf4577b21eb4"
        FROM_EMAIL = "DigiShop<donotreply@digishop.gg>"
        TO_EMAILS = [(self.__get_email(buyer))]
        message = sendgrid.Mail(
            from_email=FROM_EMAIL,
            to_emails=TO_EMAILS)

        self.cursor.execute(
            "SELECT sold_timestamp, price from sold_listings WHERE order_id = ?",
            (order_id))
        sold_timestamp, price = self.cursor.fetchone()
        # pass custom values for our HTML placeholders
        message.dynamic_template_data = {
            'orderId': order_id,
            'price': price
        }
        message.template_id = TEMPLATE_ID
        sg.send(message)


        TEMPLATE_ID = "d-13898c47cd804ab8b603e919895e7120"
        FROM_EMAIL = "DigiShop<donotreply@digishop.gg>"
        TO_EMAILS = [(self.__get_email(seller))]
        message = sendgrid.Mail(
            from_email=FROM_EMAIL,
            to_emails=TO_EMAILS)


        # pass custom values for our HTML placeholders
        message.dynamic_template_data = {
            'orderId': order_id,
            'endDate': str(datetime.datetime.fromtimestamp(int(sold_timestamp) + 604800).strftime("%m-%d-%Y"))
        }
        message.template_id = TEMPLATE_ID
        sg.send(message)

    def sale_completed(self, buyer, seller, order_id):
        sg = sendgrid.SendGridAPIClient(api_key="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")
        TEMPLATE_ID = "d-530edc468633407eab07b90bb0a73507"
        FROM_EMAIL = "DigiShop<donotreply@digishop.gg>"
        TO_EMAILS = [(self.__get_email(buyer))]
        message = sendgrid.Mail(
            from_email=FROM_EMAIL,
            to_emails=TO_EMAILS)

        self.cursor.execute(
            "SELECT price, withdraw_account, sold_timestamp, moment_id, serial from sold_listings WHERE order_id = ?",
            (order_id))
        price, withdraw_account, sold_timestamp, moment_id, momentSerial = self.cursor.fetchone()
        momentData = manager().grab_moment_by_id(moment_id)
        # pass custom values for our HTML placeholders
        message.dynamic_template_data = {
            'orderId': order_id,
            'price': str(price),
            'shipAccount': str(withdraw_account),
            'date': datetime.datetime.fromtimestamp(int(sold_timestamp)).strftime("%m-%d-%Y %H:%M"),
            'name': momentData['play']['stats']['playerName'],
            'serial': str(momentSerial) + "/" + str(momentData['circulationCount']),
            'type': momentData['play']['stats']['playCategory'],
            'set': momentData['set']['flowName'],
            'momentDate': datetime.datetime.fromisoformat(momentData['play']['stats']['dateOfMoment'][:-1]).strftime(
                '%m-%d-%Y'),
            'series': "Series " + str(momentData['set']['flowSeriesNumber']),
            'momentIcon': manager().grab_moment_icon_by_id(moment_id),
            'pendingBalance': str(round(((float(price) * 0.92) - 0.30), 2)),
            'sendEndDate': str(datetime.datetime.fromtimestamp(int(sold_timestamp) + 604800).strftime("%m-%d-%Y")),
        }
        message.template_id = TEMPLATE_ID
        sg.send(message)

        TEMPLATE_ID = "d-f40a65b7c81a4230885497d88a24af82"
        FROM_EMAIL = "DigiShop<donotreply@digishop.gg>"
        TO_EMAILS = [(self.__get_email(seller))]
        message = sendgrid.Mail(
            from_email=FROM_EMAIL,
            to_emails=TO_EMAILS)


        # pass custom values for our HTML placeholders
        message.dynamic_template_data = {
            'orderId': order_id,
            'price': str(price),
            'shipAccount': str(withdraw_account),
            'date': datetime.datetime.fromtimestamp(int(sold_timestamp)).strftime("%m-%d-%Y %H:%M"),
            'name': momentData['play']['stats']['playerName'],
            'serial': str(momentSerial) + "/" + str(momentData['circulationCount']),
            'type': momentData['play']['stats']['playCategory'],
            'set': momentData['set']['flowName'],
            'momentDate': datetime.datetime.fromisoformat(momentData['play']['stats']['dateOfMoment'][:-1]).strftime(
                '%m-%d-%Y'),
            'series': "Series " + str(momentData['set']['flowSeriesNumber']),
            'momentIcon': manager().grab_moment_icon_by_id(moment_id),
            'pendingBalance': str(round(((float(price) * 0.92) - 0.30), 2)),
        }
        message.template_id = TEMPLATE_ID
        sg.send(message)

    def payout_created(self, owner, payout_id):
        sg = sendgrid.SendGridAPIClient(api_key="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")
        TEMPLATE_ID = "d-afdf39ce78ff4192b7b3b59c53267053"
        FROM_EMAIL = "DigiShop<donotreply@digishop.gg>"
        TO_EMAILS = [(self.__get_email(owner))]
        message = sendgrid.Mail(
            from_email=FROM_EMAIL,
            to_emails=TO_EMAILS)

        self.cursor.execute(
            "SELECT withdraw_amount, withdraw_email from withdraw_requests WHERE id = ?",
            (payout_id))
        withdraw_amount, withdraw_email = self.cursor.fetchone()
        # pass custom values for our HTML placeholders
        message.dynamic_template_data = {
            'payoutId': payout_id,
            'payout': str(withdraw_amount),
            'payoutAddress': str(withdraw_email),
        }
        message.template_id = TEMPLATE_ID
        sg.send(message)

    def payout_completed(self, owner, payout_id):
        sg = sendgrid.SendGridAPIClient(api_key="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")
        TEMPLATE_ID = "d-12180153d7db41758de7c7583dd4cb0a"
        FROM_EMAIL = "DigiShop<donotreply@digishop.gg>"
        TO_EMAILS = [(self.__get_email(owner))]
        message = sendgrid.Mail(
            from_email=FROM_EMAIL,
            to_emails=TO_EMAILS)

        self.cursor.execute(
            "SELECT withdraw_amount, withdraw_email from withdraw_requests WHERE id = ?",
            (payout_id))
        withdraw_amount, withdraw_email = self.cursor.fetchone()
        # pass custom values for our HTML placeholders
        message.dynamic_template_data = {
            'payoutId': payout_id,
            'payout': str(withdraw_amount),
            'payoutAddress': str(withdraw_email),
        }
        message.template_id = TEMPLATE_ID
        sg.send(message)

    def moment_send_notice(self, owner, order_id):
        sg = sendgrid.SendGridAPIClient(api_key="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")
        TEMPLATE_ID = "d-46d53630162d4fa596c6317afb818085"
        FROM_EMAIL = "DigiShop<donotreply@digishop.gg>"
        TO_EMAILS = [(self.__get_email(owner))]
        message = sendgrid.Mail(
            from_email=FROM_EMAIL,
            to_emails=TO_EMAILS)

        self.cursor.execute(
            "SELECT price, withdraw_account, sold_timestamp, moment_id, serial from sold_listings WHERE order_id = ?",
            (order_id))
        price, withdraw_account, sold_timestamp, moment_id, momentSerial = self.cursor.fetchone()
        momentData = manager().grab_moment_by_id(moment_id)
        # pass custom values for our HTML placeholders
        message.dynamic_template_data = {
            'orderId': order_id,
            'price': str(price),
            'shipAccount': str(withdraw_account),
            'date': datetime.datetime.fromtimestamp(int(sold_timestamp)).strftime("%m-%d-%Y %H:%M"),
            'name': momentData['play']['stats']['playerName'],
            'serial': str(momentSerial) + "/" + str(momentData['circulationCount']),
            'type': momentData['play']['stats']['playCategory'],
            'set': momentData['set']['flowName'],
            'momentDate': datetime.datetime.fromisoformat(momentData['play']['stats']['dateOfMoment'][:-1]).strftime(
                '%m-%d-%Y'),
            'series': "Series " + str(momentData['set']['flowSeriesNumber']),
            'momentIcon': manager().grab_moment_icon_by_id(moment_id),
            'pendingBalance': str(round(((float(price) * 0.92) - 0.30), 2)),
            'sendEndDate': str(datetime.datetime.fromtimestamp(int(sold_timestamp) + 604800).strftime("%m-%d-%Y")),
            'daysRemaining': math.floor(((int(sold_timestamp) + 604800) - int(datetime.datetime.now().timestamp())) / 86400)
        }
        message.template_id = TEMPLATE_ID
        sg.send(message)

e = emailer()
e.moment_send_notice('jdefesche', '3534sdffd')
