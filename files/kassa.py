#!/usr/bin/env python3

# Скрипт проведения платежа Яндекс.Касса
# описание протокола https://kassa.yandex.ru/docs/checkout-api/

import json
import logging
import sys
from datetime import datetime

sys.path.insert(0, "/usr/local/billing/payments")  # NOQA
import lbsoap  # NOQA

# Настройки логирования
YANDEX_LOG = '/var/log/billing/weblogs/yandex.kassa.log'
logging.basicConfig(filename=YANDEX_LOG, level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s:  %(message)s'
                    )

# Параметры подключения к LBcore
HOST = '127.0.0.1'
PORT = 34012
MANAGER = 'yandex'
PASSWORD = 'yandex'

# Класс платежа (id) из таблицы pay_classses
CLASS_ID = 0

# Получение данных от сервера кассы
params = sys.stdin.read()
form = json.loads(params)

logging.debug('"%s"', params)
logging.debug('"%s"', form)


def payment_handler() -> bool:
    success: str = form["object"]["status"]  # Статус платежа
    id: str = form["object"]["id"]  # Идентификатор платежа
    amount: float = float(form["object"]["amount"]["value"])  # Сумма в выбранной валюте
    pre_payment_id: int = int(form["object"]["metadata"]["payment_id"])  # Идентификатор предварительного платежа в АСР
    auto_pay: bool = form["object"]["payment_method"]["saved"]  # Флаг подключения рекуррентного платежа
    payment_method_id: str = form["object"]["payment_method"]["id"]  # Идентификатор способа оплаты
    created_at: datetime = datetime.strptime(form["object"]["created_at"],
                                             "%Y-%m-%dT%H:%M:%S.%fZ")  # Дата создания платежа

    soap_client = lbsoap.Client()
    if not soap_client.connect(HOST, PORT) or not soap_client.login(MANAGER, PASSWORD):
        return False
    if success == str("succeeded"):
        # Проведение платежа
        ret, _ = soap_client.confirmPrePayment(pre_payment_id, CLASS_ID, 2, amount, id, created_at, '')
        if ret != lbsoap.Result.OK:
            return False
        ret, payment = soap_client.getPrePayment(pre_payment_id, -1)
        if ret != lbsoap.Result.OK:
            return False
        logging.debug(payment)

        if auto_pay:
            ret, params = soap_client.getEpsAgreementsParams('', payment_method_id)
            if ret != lbsoap.Result.OK:
                return False

            record_id = 0
            agrm_id = 0
            if len(params) > 0:
                if params[0]['status'] > 0:
                    logging.debug("Autopayment already enabled")
                    return True
                record_id = params[0]['record_id']
            else:
                agrm_id = payment["agrm_id"]

            ret, _ = soap_client.setEpsAgreementsParam(payment_method_id, 1, '', '', record_id, agrm_id)

            if ret != lbsoap.Result.OK:
                logging.debug("Autopayment not enabled")
                return False
            logging.debug("Autopayment is enabled")

    elif success == "canceled":
        reason: str = form["object"]["cancellation_details"]["reason"]
        if reason == "permission_revoked":
            ret, params = soap_client.getEpsAgreementsParams('', payment_method_id)
            if ret != lbsoap.Result.OK:
                return False
            if len(params) > 0 and params[0]['status'] > 0:
                ret = soap_client.delEpsAgreementsParams(params[0]['record_id'])
            if ret != lbsoap.Result.OK:
                logging.debug("Autopayment not disabled")
                return False
            logging.debug("Autopayment is disabled")
        else:
            ret, payment = soap_client.getPrePayment(pre_payment_id, -1)
            if ret == lbsoap.Result.NOT_FOUND:
                return True
            if ret != lbsoap.Result.OK:
                return False
            soap_client.cancelPrePayment(pre_payment_id, datetime.now())

    return True


def refund_handler() -> bool:
    payment_id: int = int(form["object"]["payment_id"])  # Идентификатор платежа в АСР
    created_at: datetime = datetime.strptime(form["object"]["created_at"],
                                             "%Y-%m-%dT%H:%M:%S.%fZ")  # Дата создания платежа
    soap_client = lbsoap.Client()
    if not soap_client.connect(HOST, PORT) or not soap_client.login(MANAGER, PASSWORD):
        return False
    soap_client.cancel(payment_id, created_at)
    return True


def handler():
    event: str = form.get("event")
    if event.startswith('payment.'):
        return payment_handler()
    if event.startswith('refund.'):
        return refund_handler()
    return True


if handler():
    print('Status: 200\n\n')
    print('Content-type: text/html\n\n')
    logging.info('Ok')
