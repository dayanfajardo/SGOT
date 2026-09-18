from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.customers.models import Customer


class CustomerModelTests(TestCase):
    def test_create_customer(self):
        customer = Customer.objects.create(
            customer_code="C-1001",
            code_system=Customer.CodeSystem.CENTURION,
            trade_name="Alarmas del Norte",
            legal_name="Alarmas del Norte S.A.S.",
            document="900123456-1",
            phone="3001234567",
            email="contacto@alarmasdelnorte.test",
        )

        self.assertIsNotNone(customer.pk)
        self.assertEqual(customer.trade_name, "Alarmas del Norte")
        self.assertEqual(customer.customer_code, "C-1001")
        self.assertEqual(customer.code_system, Customer.CodeSystem.CENTURION)

    def test_str_returns_trade_name(self):
        customer = Customer.objects.create(trade_name="Seguridad Andina")

        self.assertEqual(str(customer), "Seguridad Andina")

    def test_ordering_by_trade_name(self):
        Customer.objects.create(trade_name="Zeta Protección")
        Customer.objects.create(trade_name="Alfa Alarmas")
        Customer.objects.create(trade_name="Norte Electrónica")

        names = list(Customer.objects.values_list("trade_name", flat=True))

        self.assertEqual(
            names,
            ["Alfa Alarmas", "Norte Electrónica", "Zeta Protección"],
        )

    def test_unique_code_system_and_customer_code(self):
        Customer.objects.create(
            customer_code="C-2002",
            code_system=Customer.CodeSystem.CENTURION,
            trade_name="Cliente Original",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Customer.objects.create(
                    customer_code="C-2002",
                    code_system=Customer.CodeSystem.CENTURION,
                    trade_name="Cliente Duplicado",
                )

    def test_same_customer_code_allowed_in_different_systems(self):
        centurion_customer = Customer.objects.create(
            customer_code="C-3003",
            code_system=Customer.CodeSystem.CENTURION,
            trade_name="Cliente Centurión",
        )
        arion_customer = Customer.objects.create(
            customer_code="C-3003",
            code_system=Customer.CodeSystem.ARION,
            trade_name="Cliente Arion",
        )

        self.assertNotEqual(centurion_customer.pk, arion_customer.pk)
        self.assertEqual(
            Customer.objects.filter(customer_code="C-3003").count(),
            2,
        )
