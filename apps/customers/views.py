from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.customers.forms import CustomerFilterForm, CustomerForm
from apps.customers.models import Customer


@login_required
def customer_list(request):
    if not request.user.has_perm("customers.view_customer"):
        raise PermissionDenied

    customers = Customer.objects.all()
    has_customers = customers.exists()
    filter_form = CustomerFilterForm(request.GET or None)

    if filter_form.is_valid():
        q = filter_form.cleaned_data.get("q")
        if q:
            customers = customers.filter(
                Q(trade_name__icontains=q)
                | Q(legal_name__icontains=q)
                | Q(document__icontains=q)
                | Q(customer_code__icontains=q)
                | Q(email__icontains=q)
            )
        code_system = filter_form.cleaned_data.get("code_system")
        if code_system:
            customers = customers.filter(code_system=code_system)

    return render(
        request,
        "customers/customer_list.html",
        {
            "customers": customers,
            "filter_form": filter_form,
            "has_customers": has_customers,
        },
    )


@login_required
def customer_detail(request, pk):
    if not request.user.has_perm("customers.view_customer"):
        raise PermissionDenied

    customer = get_object_or_404(Customer, pk=pk)
    return render(
        request,
        "customers/customer_detail.html",
        {"customer": customer},
    )


def _customer_form(request, *, customer=None):
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save()
            return redirect("customers:customer_detail", pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)

    return render(
        request,
        "customers/customer_form.html",
        {
            "form": form,
            "customer": customer,
            "is_edit": customer is not None,
        },
    )


@login_required
def customer_create(request):
    if not request.user.has_perm("customers.add_customer"):
        raise PermissionDenied

    return _customer_form(request)


@login_required
def customer_update(request, pk):
    if not request.user.has_perm("customers.change_customer"):
        raise PermissionDenied

    customer = get_object_or_404(Customer, pk=pk)
    return _customer_form(request, customer=customer)
