# coding=utf-8
from __future__ import unicode_literals

import datetime

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from contact_verification import settings
from contact_verification.models import ContactVerification, Contact


def minify_phone_number(phone_number):
    if phone_number.isdigit() and len(phone_number) > 0 and phone_number[0] == '0':
        phone_number = phone_number[1:]
    return phone_number


class ContactVerificationSerializer(serializers.ModelSerializer):
    message = None

    class Meta:
        model = ContactVerification
        fields = ['country_number', 'phone_number']
        extra_kwargs = {
            'phone_number': {
                'error_messages': {'blank': _("전화번호를 입력하세요.")}
            }
        }

    def validate_phone_number(self, value):
        return minify_phone_number(value)

    def validate(self, attrs):
        ContactVerification.objects.inactive().delete()

        try:
            pin = ContactVerification.objects.get(**attrs)
        except ContactVerification.DoesNotExist:
            pin = None

        if pin and pin.is_awaiting():
            seconds = (datetime.timedelta(minutes=3)-(timezone.now() - pin.created)).seconds
            raise serializers.ValidationError(_("인증코드가 이미 전송되었습니다. %(seconds)s초 후에 재발송 가능합니다.") % {'seconds': seconds})

        if Contact.objects.filter(**attrs).exists():
            raise serializers.ValidationError(_("이미 인증된 번호입니다."))

        return attrs

    def create(self, validated_data):
        instance = super(ContactVerificationSerializer, self).create(validated_data)

        # message = settings.CONTACT_VERIFICATION_SMS_TEXT.format(code=pin.code)
        # is_success = send_sms(message, str(contact), str(settings.CONTACT_VERIFICATION_SENDER))
        is_success = True

        if is_success:
            self.message = _("인증코드를 전송하였습니다.")
        else:
            instance.delete()
            raise serializers.ValidationError({'message': _("인증코드 전송을 실패하였습니다.")})
        return instance

    def to_representation(self, instance):
        ret = super(ContactVerificationSerializer, self).to_representation(instance)
        if self.message:
            ret['message'] = self.message
        return ret


class ContactSerializer(serializers.ModelSerializer):
    code = serializers.CharField(write_only=True, error_messages= {'blank': _("인증번호를 입력하세요.")})

    class Meta:
        model = Contact
        fields = ['country_number', 'phone_number', 'code']
        extra_kwargs = {
            'phone_number': {
                'error_messages': {'blank': _("전화번호를 입력하세요.")}
            }
        }
        validators = [
            UniqueTogetherValidator(
                queryset=Contact.objects.all(),
                fields=['country_number', 'phone_number'],
                message=_("이미 인증된 번호입니다.")
            )
        ]

    def validate_phone_number(self, value):
        return minify_phone_number(value)

    def validate(self, attrs):
        if not ContactVerification.objects.awaiting().filter(**attrs).exists():
            raise serializers.ValidationError(_("인증번호 또는 전화번호가 올바르지 않습니다."))
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        ContactVerification.objects.awaiting().filter(**validated_data).delete()
        if not settings.CONTACT_VERIFICATION_ALLOW_MULTIPLE_CONTACTS:
            user.contacts.all().delete()
        validated_data['user'] = user
        validated_data.pop('code', None)
        return super(ContactSerializer, self).create(validated_data)


class CountrySerializer(serializers.Serializer):
    number = serializers.CharField()
    name = serializers.CharField()