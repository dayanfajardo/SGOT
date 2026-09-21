from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.catalog.models import Product, Technician, WorkType


class ProductModelTests(TestCase):
    def test_create_product(self):
        product = Product.objects.create(
            name="Cámara IP 4MP",
            reference="CAM-4MP-001",
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )

        self.assertIsNotNone(product.pk)
        self.assertEqual(product.name, "Cámara IP 4MP")
        self.assertEqual(product.reference, "CAM-4MP-001")
        self.assertTrue(product.active)

    def test_str_returns_name(self):
        product = Product.objects.create(
            name="Cable UTP Cat6",
            product_type=Product.ProductType.MATERIAL,
            unit=Product.Unit.METER,
        )

        self.assertEqual(str(product), "Cable UTP Cat6")

    def test_ordering_by_name(self):
        Product.objects.create(
            name="Sensor PIR",
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )
        Product.objects.create(
            name="Alarma perimetral",
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )
        Product.objects.create(
            name="DVR 8 canales",
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )

        names = list(Product.objects.values_list("name", flat=True))

        self.assertEqual(
            names,
            ["Alarma perimetral", "DVR 8 canales", "Sensor PIR"],
        )

    def test_product_types_equipment_and_material(self):
        equipment = Product.objects.create(
            name="DVR 16 canales",
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )
        material = Product.objects.create(
            name="Conector BNC",
            product_type=Product.ProductType.MATERIAL,
            unit=Product.Unit.UNIT,
        )

        self.assertEqual(equipment.product_type, Product.ProductType.EQUIPMENT)
        self.assertEqual(material.product_type, Product.ProductType.MATERIAL)

    def test_unit_choices_can_be_assigned(self):
        unit_product = Product.objects.create(
            name="Fuente 12V",
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )
        meter_product = Product.objects.create(
            name="Cable coaxial RG59",
            product_type=Product.ProductType.MATERIAL,
            unit=Product.Unit.METER,
        )
        roll_product = Product.objects.create(
            name="Cinta aislante",
            product_type=Product.ProductType.MATERIAL,
            unit=Product.Unit.ROLL,
        )
        box_product = Product.objects.create(
            name="Tornillos 8 mm",
            product_type=Product.ProductType.MATERIAL,
            unit=Product.Unit.BOX,
        )

        self.assertEqual(unit_product.unit, Product.Unit.UNIT)
        self.assertEqual(meter_product.unit, Product.Unit.METER)
        self.assertEqual(roll_product.unit, Product.Unit.ROLL)
        self.assertEqual(box_product.unit, Product.Unit.BOX)


class TechnicianModelTests(TestCase):
    def test_create_technician(self):
        technician = Technician.objects.create(
            first_name="Carlos",
            last_name="Pérez",
            phone="3101234567",
            technician_type=Technician.TechnicianType.STAFF,
        )

        self.assertIsNotNone(technician.pk)
        self.assertEqual(technician.first_name, "Carlos")
        self.assertEqual(technician.last_name, "Pérez")
        self.assertEqual(technician.phone, "3101234567")
        self.assertTrue(technician.active)

    def test_str_returns_full_name_without_extra_spaces(self):
        with_last_name = Technician.objects.create(
            first_name="Ana",
            last_name="Gómez",
            technician_type=Technician.TechnicianType.STAFF,
        )
        without_last_name = Technician.objects.create(
            first_name="Luis",
            technician_type=Technician.TechnicianType.CONTRACTOR,
        )

        self.assertEqual(str(with_last_name), "Ana Gómez")
        self.assertEqual(str(without_last_name), "Luis")

    def test_technician_can_be_staff_or_contractor(self):
        staff = Technician.objects.create(
            first_name="Marta",
            last_name="Ruiz",
            technician_type=Technician.TechnicianType.STAFF,
        )
        contractor = Technician.objects.create(
            first_name="Diego",
            last_name="Vargas",
            technician_type=Technician.TechnicianType.CONTRACTOR,
        )

        self.assertEqual(staff.technician_type, Technician.TechnicianType.STAFF)
        self.assertEqual(
            contractor.technician_type,
            Technician.TechnicianType.CONTRACTOR,
        )

    def test_ordering_by_first_name_and_last_name(self):
        Technician.objects.create(
            first_name="Pedro",
            last_name="López",
            technician_type=Technician.TechnicianType.STAFF,
        )
        Technician.objects.create(
            first_name="Ana",
            last_name="Torres",
            technician_type=Technician.TechnicianType.STAFF,
        )
        Technician.objects.create(
            first_name="Ana",
            last_name="Díaz",
            technician_type=Technician.TechnicianType.CONTRACTOR,
        )

        names = [
            (tech.first_name, tech.last_name)
            for tech in Technician.objects.all()
        ]

        self.assertEqual(
            names,
            [
                ("Ana", "Díaz"),
                ("Ana", "Torres"),
                ("Pedro", "López"),
            ],
        )


class WorkTypeModelTests(TestCase):
    def test_create_work_type(self):
        work_type = WorkType.objects.create(
            name="Mantenimiento preventivo",
            description="Revisión periódica de equipos",
        )

        self.assertIsNotNone(work_type.pk)
        self.assertEqual(work_type.name, "Mantenimiento preventivo")
        self.assertEqual(work_type.description, "Revisión periódica de equipos")
        self.assertTrue(work_type.active)

    def test_str_returns_name(self):
        work_type = WorkType.objects.create(name="Instalación de CCTV")

        self.assertEqual(str(work_type), "Instalación de CCTV")

    def test_ordering_by_name(self):
        WorkType.objects.create(name="Soporte técnico")
        WorkType.objects.create(name="Instalación")
        WorkType.objects.create(name="Mantenimiento")

        names = list(WorkType.objects.values_list("name", flat=True))

        self.assertEqual(
            names,
            ["Instalación", "Mantenimiento", "Soporte técnico"],
        )

    def test_unique_name(self):
        WorkType.objects.create(name="Revisión de alarma")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WorkType.objects.create(name="Revisión de alarma")
