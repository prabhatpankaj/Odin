from rest_framework import serializers

from django.core.exceptions import ValidationError
from django.db.models.query import Q
from django.db import transaction
from django.utils import timezone

from odin.emails.services import send_mail

from odin.users.models import BaseUser, Profile, PasswordResetToken


class _ProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.FileField(source='full_image')

    class Meta:
        model = Profile
        fields = ('full_name', 'avatar')


class _UserSerializer(serializers.ModelSerializer):

    user_type = serializers.SerializerMethodField()

    class Meta:
        model = BaseUser
        fields = (
            'id',
            'email',
            'user_type'
            )

    def get_user_type(self, obj):
        if obj.is_teacher():
            return 'teacher'
        elif obj.is_student():
            return 'student'


def get_user_data(*, user: BaseUser):
    user_data = _UserSerializer(instance=user).data
    profile_data = _ProfileSerializer(instance=user.profile).data

    return {**user_data, **profile_data}


@transaction.atomic
def logout(*, user: BaseUser) -> BaseUser:
    user.rotate_secret_key()

    return user


@transaction.atomic
def initiate_reset_user_password(*, user: BaseUser) -> PasswordResetToken:
    if not user.is_active:
        raise ValidationError('Cannot reset password for inactive user')

    now = timezone.now()
    query = Q(user=user) & (Q(voided_at__isnull=True) | Q(used_at__isnull=True))
    PasswordResetToken.objects.filter(query).update(voided_at=now)

    password_reset_token = PasswordResetToken.objects.create(user=user)

    reset_link = f'https://academy.hacksoft.io/forgot-password/{str(password_reset_token.token)}/'

    send_mail(
        recipients=[user.email],
        template_name='account_email_password_reset_key',
        context={
            'password_reset_url': reset_link
        }
    )

    return token


@transaction.atomic
def reset_user_password(
    *,
    token: PasswordResetToken,
    password: str
) -> BaseUser:
    if token.used or token.voided:
        raise ValidationError('Invalid reset password token.')

    user = token.user

    user.set_password(password)
    user.rotate_secret_key()

    user.save()

    token.use()

    return user
