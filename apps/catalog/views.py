from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.catalog.forms import (
    ProductFilterForm,
    ProductForm,
    TechnicianFilterForm,
    TechnicianForm,
    WorkTypeFilterForm,
    WorkTypeForm,
)
from apps.catalog.models import Product, Technician, WorkType


@login_required
def worktype_list(request):
    if not request.user.has_perm("catalog.view_worktype"):
        raise PermissionDenied

    worktypes = WorkType.objects.all()
    has_worktypes = worktypes.exists()
    filter_form = WorkTypeFilterForm(request.GET or None)

    if filter_form.is_valid():
        q = filter_form.cleaned_data.get("q")
        if q:
            worktypes = worktypes.filter(
                Q(name__icontains=q) | Q(description__icontains=q)
            )

        active = filter_form.cleaned_data.get("active")
        if active == "1":
            worktypes = worktypes.filter(active=True)
        elif active == "0":
            worktypes = worktypes.filter(active=False)

    return render(
        request,
        "catalog/worktype_list.html",
        {
            "worktypes": worktypes,
            "filter_form": filter_form,
            "has_worktypes": has_worktypes,
        },
    )


@login_required
def worktype_detail(request, pk):
    if not request.user.has_perm("catalog.view_worktype"):
        raise PermissionDenied

    worktype = get_object_or_404(WorkType, pk=pk)
    return render(
        request,
        "catalog/worktype_detail.html",
        {"worktype": worktype},
    )


def _worktype_form(request, *, worktype=None):
    if request.method == "POST":
        form = WorkTypeForm(request.POST, instance=worktype)
        if form.is_valid():
            worktype = form.save()
            return redirect("catalog:worktype_detail", pk=worktype.pk)
    else:
        form = WorkTypeForm(instance=worktype)

    return render(
        request,
        "catalog/worktype_form.html",
        {
            "form": form,
            "worktype": worktype,
            "is_edit": worktype is not None,
        },
    )


@login_required
def worktype_create(request):
    if not request.user.has_perm("catalog.add_worktype"):
        raise PermissionDenied

    return _worktype_form(request)


@login_required
def worktype_update(request, pk):
    if not request.user.has_perm("catalog.change_worktype"):
        raise PermissionDenied

    worktype = get_object_or_404(WorkType, pk=pk)
    return _worktype_form(request, worktype=worktype)


@login_required
@require_POST
def worktype_toggle_active(request, pk):
    if not request.user.has_perm("catalog.change_worktype"):
        raise PermissionDenied

    worktype = get_object_or_404(WorkType, pk=pk)
    worktype.active = not worktype.active
    worktype.save(update_fields=["active"])
    return redirect("catalog:worktype_detail", pk=worktype.pk)


@login_required
def technician_list(request):
    if not request.user.has_perm("catalog.view_technician"):
        raise PermissionDenied

    technicians = Technician.objects.all()
    has_technicians = technicians.exists()
    filter_form = TechnicianFilterForm(request.GET or None)

    if filter_form.is_valid():
        q = filter_form.cleaned_data.get("q")
        if q:
            technicians = technicians.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(phone__icontains=q)
            )

        technician_type = filter_form.cleaned_data.get("technician_type")
        if technician_type:
            technicians = technicians.filter(technician_type=technician_type)

        active = filter_form.cleaned_data.get("active")
        if active == "1":
            technicians = technicians.filter(active=True)
        elif active == "0":
            technicians = technicians.filter(active=False)

    return render(
        request,
        "catalog/technician_list.html",
        {
            "technicians": technicians,
            "filter_form": filter_form,
            "has_technicians": has_technicians,
        },
    )


@login_required
def technician_detail(request, pk):
    if not request.user.has_perm("catalog.view_technician"):
        raise PermissionDenied

    technician = get_object_or_404(Technician, pk=pk)
    return render(
        request,
        "catalog/technician_detail.html",
        {"technician": technician},
    )


def _technician_form(request, *, technician=None):
    if request.method == "POST":
        form = TechnicianForm(request.POST, instance=technician)
        if form.is_valid():
            technician = form.save()
            return redirect("catalog:technician_detail", pk=technician.pk)
    else:
        form = TechnicianForm(instance=technician)

    return render(
        request,
        "catalog/technician_form.html",
        {
            "form": form,
            "technician": technician,
            "is_edit": technician is not None,
        },
    )


@login_required
def technician_create(request):
    if not request.user.has_perm("catalog.add_technician"):
        raise PermissionDenied

    return _technician_form(request)


@login_required
def technician_update(request, pk):
    if not request.user.has_perm("catalog.change_technician"):
        raise PermissionDenied

    technician = get_object_or_404(Technician, pk=pk)
    return _technician_form(request, technician=technician)


@login_required
def product_list(request):
    if not request.user.has_perm("catalog.view_product"):
        raise PermissionDenied

    products = Product.objects.all()
    has_products = products.exists()
    filter_form = ProductFilterForm(request.GET or None)

    if filter_form.is_valid():
        q = filter_form.cleaned_data.get("q")
        if q:
            products = products.filter(
                Q(product_code__icontains=q)
                | Q(name__icontains=q)
                | Q(reference__icontains=q)
            )

        category = filter_form.cleaned_data.get("category")
        if category:
            products = products.filter(category=category)

        product_type = filter_form.cleaned_data.get("product_type")
        if product_type:
            products = products.filter(product_type=product_type)

        active = filter_form.cleaned_data.get("active")
        if active == "1":
            products = products.filter(active=True)
        elif active == "0":
            products = products.filter(active=False)

    return render(
        request,
        "catalog/product_list.html",
        {
            "products": products,
            "filter_form": filter_form,
            "has_products": has_products,
        },
    )


@login_required
def product_detail(request, pk):
    if not request.user.has_perm("catalog.view_product"):
        raise PermissionDenied

    product = get_object_or_404(Product, pk=pk)
    return render(
        request,
        "catalog/product_detail.html",
        {"product": product},
    )


def _product_form(request, *, product=None):
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            return redirect("catalog:product_detail", pk=product.pk)
    else:
        form = ProductForm(instance=product)

    return render(
        request,
        "catalog/product_form.html",
        {
            "form": form,
            "product": product,
            "is_edit": product is not None,
        },
    )


@login_required
def product_create(request):
    if not request.user.has_perm("catalog.add_product"):
        raise PermissionDenied

    return _product_form(request)


@login_required
def product_update(request, pk):
    if not request.user.has_perm("catalog.change_product"):
        raise PermissionDenied

    product = get_object_or_404(Product, pk=pk)
    return _product_form(request, product=product)


@login_required
@require_POST
def product_toggle_active(request, pk):
    if not request.user.has_perm("catalog.change_product"):
        raise PermissionDenied

    product = get_object_or_404(Product, pk=pk)
    product.active = not product.active
    product.save(update_fields=["active"])
    return redirect("catalog:product_detail", pk=product.pk)


@login_required
@require_POST
def technician_toggle_active(request, pk):
    if not request.user.has_perm("catalog.change_technician"):
        raise PermissionDenied

    technician = get_object_or_404(Technician, pk=pk)
    technician.active = not technician.active
    technician.save(update_fields=["active"])
    return redirect("catalog:technician_detail", pk=technician.pk)
