from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.forms import (
    UserCreateForm,
    UserFilterForm,
    UserResetPasswordForm,
    UserUpdateForm,
)

User = get_user_model()


@login_required
def user_list(request):
    if not request.user.has_perm("accounts.view_user"):
        raise PermissionDenied

    users = User.objects.prefetch_related("groups").all()
    has_users = users.exists()
    filter_form = UserFilterForm(request.GET or None)

    if filter_form.is_valid():
        q = filter_form.cleaned_data.get("q")
        if q:
            users = users.filter(
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
            )
        role = filter_form.cleaned_data.get("role")
        if role:
            users = users.filter(groups__name=role).distinct()
        active = filter_form.cleaned_data.get("active")
        if active == "1":
            users = users.filter(is_active=True)
        elif active == "0":
            users = users.filter(is_active=False)

    users = users.order_by("first_name", "last_name", "username")

    return render(
        request,
        "accounts/user_list.html",
        {
            "users": users,
            "filter_form": filter_form,
            "has_users": has_users,
        },
    )


@login_required
def user_detail(request, pk):
    if not request.user.has_perm("accounts.view_user"):
        raise PermissionDenied

    managed_user = get_object_or_404(
        User.objects.prefetch_related("groups"),
        pk=pk,
    )
    return render(
        request,
        "accounts/user_detail.html",
        {"managed_user": managed_user},
    )


@login_required
def user_create(request):
    if not request.user.has_perm("accounts.add_user"):
        raise PermissionDenied

    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            managed_user = form.save()
            return redirect("accounts:user_detail", pk=managed_user.pk)
    else:
        form = UserCreateForm()

    return render(
        request,
        "accounts/user_form.html",
        {
            "form": form,
            "is_edit": False,
        },
    )


@login_required
def user_update(request, pk):
    if not request.user.has_perm("accounts.change_user"):
        raise PermissionDenied

    managed_user = get_object_or_404(
        User.objects.prefetch_related("groups"),
        pk=pk,
    )
    if request.method == "POST":
        form = UserUpdateForm(
            request.POST,
            instance=managed_user,
            requesting_user=request.user,
        )
        if form.is_valid():
            managed_user = form.save()
            return redirect("accounts:user_detail", pk=managed_user.pk)
    else:
        form = UserUpdateForm(
            instance=managed_user,
            requesting_user=request.user,
        )

    return render(
        request,
        "accounts/user_form.html",
        {
            "form": form,
            "managed_user": managed_user,
            "is_edit": True,
        },
    )


@login_required
@require_POST
def user_toggle_active(request, pk):
    if not request.user.has_perm("accounts.change_user"):
        raise PermissionDenied

    managed_user = get_object_or_404(User, pk=pk)
    if request.user.pk == managed_user.pk and managed_user.is_active:
        messages.error(request, "No puedes desactivar tu propia cuenta.")
        return redirect("accounts:user_detail", pk=managed_user.pk)

    managed_user.is_active = not managed_user.is_active
    managed_user.save(update_fields=["is_active"])
    return redirect("accounts:user_detail", pk=managed_user.pk)


@login_required
def user_reset_password(request, pk):
    if not request.user.has_perm("accounts.change_user"):
        raise PermissionDenied

    managed_user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserResetPasswordForm(managed_user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, managed_user)
            return redirect("accounts:user_detail", pk=managed_user.pk)
    else:
        form = UserResetPasswordForm(managed_user)

    return render(
        request,
        "accounts/password_reset_form.html",
        {
            "form": form,
            "managed_user": managed_user,
        },
    )
