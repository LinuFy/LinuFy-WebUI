# -*- coding: utf-8 -*-

import uuid
import secrets
from os.path import exists
from flask import session
from flask_login import UserMixin, current_user
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import inspect

from linufy.app import db


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses Postgresql's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)

        if not isinstance(value, uuid.UUID):
            return "%.32x" % uuid.UUID(value).int
        # hexstring
        return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(value)


class Configuration(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(1000))
    value = db.Column(db.Text())


class Organization(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(1000), unique=True)
    type_of = db.Column(db.String(10))
    allowed_support = db.Column(db.Boolean(), default=False)


class Role(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    role = db.Column(db.String(50))
    organization_id = db.Column(GUID, db.ForeignKey('organization.id'), nullable=False)
    protected = db.Column(db.Boolean(), default=False)
    by_default = db.Column(db.Boolean(), default=False)

    organization = db.relationship("Organization", foreign_keys=[organization_id])


class Ability(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(50), unique=True)


class RoleAbility(db.Model):
    __tablename__ = 'role_ability'
    role_id = db.Column(GUID, db.ForeignKey('role.id', ondelete="CASCADE"),
                        primary_key=True, nullable=False)
    ability_id = db.Column(GUID, db.ForeignKey(
        'ability.id'), primary_key=True, nullable=False)

    role = db.relationship("Role", foreign_keys=[role_id])
    ability = db.relationship("Ability", foreign_keys=[ability_id])


class User(UserMixin, db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    role_id = db.Column(GUID, db.ForeignKey('role.id'), nullable=False)
    organization_id = db.Column(GUID, db.ForeignKey('organization.id'), nullable=False)
    mfa_hash = db.Column(db.String(50))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    meta = db.relationship("UserMeta", backref='user', cascade='all, delete, delete-orphan')
    role = db.relationship("Role", foreign_keys=[role_id])
    organization = db.relationship("Organization", foreign_keys=[organization_id])

    @property
    def get_organization(self):
        if 'support_organization_id' in session:
            return session['support_organization_id']
        else:
            return current_user.organization_id


class UserMeta(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(GUID, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(1000))
    value = db.Column(db.Text())


class ApiKey(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(GUID, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(1000))
    key = db.Column(db.String(32), default=secrets.token_hex(32))
    permission = db.Column(db.String(10), default="read")

    user = db.relationship("User", foreign_keys=[user_id])


class Notification(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    object_type = db.Column(db.String(50))
    object_user_id = db.Column(GUID, db.ForeignKey('user.id'), nullable=True)
    user_id = db.Column(GUID, db.ForeignKey('user.id'), nullable=True)
    ability_id = db.Column(GUID, db.ForeignKey('ability.id'), nullable=True)
    message = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())

    ability = db.relationship("Ability", foreign_keys=[ability_id])


class Region(UserMixin, db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(1000))
    description = db.Column(db.Text())
    access_key = db.Column(db.String(16), default=secrets.token_hex(16))
    secret_key = db.Column(db.String(32), default=secrets.token_hex(32))
    organization_id = db.Column(GUID, db.ForeignKey('organization.id'), nullable=False)
    redis_id = db.Column(GUID, db.ForeignKey('redis.id'), nullable=False)
    redis_db = db.Column(db.Integer())

    organization = db.relationship("Organization", foreign_keys=[organization_id])
    redis = db.relationship("Redis", foreign_keys=[redis_id])


    @property
    def get_organization(self):
        return current_user.organization_id


class Redis(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(1000))
    description = db.Column(db.Text())
    hostname = db.Column(db.String(1000))
    port = db.Column(db.Integer())
    db_number = db.Column(db.Integer())


class Subnet(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    vlan = db.Column(db.Integer())
    name = db.Column(db.String(1000))
    description = db.Column(db.Text())
    subnet = db.Column(db.String(128))
    mask = db.Column(db.String(128))
    ip_type = db.Column(db.String(4))
    region_id = db.Column(GUID, db.ForeignKey('region.id'), nullable=False)
    organization_id = db.Column(GUID, db.ForeignKey('organization.id'), nullable=False)
    gateway_id = db.Column(GUID, db.ForeignKey('ip_address.id'), nullable=True)
    gateway = db.relationship("IPAddress", foreign_keys=[gateway_id])
    region = db.relationship("Region", foreign_keys=[region_id])
    organization = db.relationship("Organization", foreign_keys=[organization_id])

class IPAddress(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(1000))
    description = db.Column(db.Text())
    ip_address = db.Column(db.String(128))
    reserved = db.Column(db.Boolean())
    used = db.Column(db.Boolean())
    subnet_id = db.Column(GUID, db.ForeignKey('subnet.id'), nullable=False)

    subnet = db.relationship("Subnet", foreign_keys=[subnet_id])


class PasswordManagerGroup(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(1000))
    description = db.Column(db.Text())
    organization_id = db.Column(GUID, db.ForeignKey('organization.id'), nullable=False)

    organization = db.relationship("Organization", foreign_keys=[organization_id])
    password = db.relationship("PasswordManager", back_populates='group')


class PasswordManagerGroupRole(db.Model):
    role_id = db.Column(GUID, db.ForeignKey('role.id'),
                        primary_key=True, nullable=False)
    password_manager_group_id = db.Column(GUID, db.ForeignKey(
        'password_manager_group.id'), primary_key=True, nullable=False)

    role = db.relationship("Role", foreign_keys=[role_id])
    password_manager_group = db.relationship("PasswordManagerGroup", foreign_keys=[password_manager_group_id])


class PasswordManager(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(1000))
    description = db.Column(db.Text())
    username = db.Column(db.String(1000))
    password = db.Column(db.Text())
    url = db.Column(db.Text())
    group_id = db.Column(GUID, db.ForeignKey('password_manager_group.id'), nullable=False)

    group = db.relationship("PasswordManagerGroup", foreign_keys=[group_id])


class AssetGroup(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(1000))
    description = db.Column(db.Text())
    organization_id = db.Column(GUID, db.ForeignKey('organization.id'), nullable=False)

    organization = db.relationship("Organization", foreign_keys=[organization_id])


class Asset(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(1000))
    description = db.Column(db.Text())
    organization_id = db.Column(GUID, db.ForeignKey('organization.id'), nullable=False)
    ip_address_id = db.Column(GUID, db.ForeignKey('ip_address.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    organization = db.relationship("Organization", foreign_keys=[organization_id])
    ip_address = db.relationship("IPAddress", foreign_keys=[ip_address_id])
    meta = db.relationship("AssetMeta", backref='user', cascade='all, delete, delete-orphan')


class AssetMeta(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    asset_id = db.Column(GUID, db.ForeignKey('asset.id', ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(1000))
    value = db.Column(db.Text(16777216))


class AssetSystemUser(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    asset_id = db.Column(GUID, db.ForeignKey('asset.id', ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(1000))
    uid = db.Column(db.Integer())
    gid = db.Column(db.Integer())
    description = db.Column(db.String(1000))
    homedir = db.Column(db.String(1000))
    shell = db.Column(db.String(1000))


class AssetSystemGroup(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    asset_id = db.Column(GUID, db.ForeignKey('asset.id', ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(1000))
    gid = db.Column(db.Integer())


class AssetSystemStorage(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    asset_id = db.Column(GUID, db.ForeignKey('asset.id', ondelete="CASCADE"), nullable=False)
    filesystem = db.Column(db.String(1000))
    mountpoint = db.Column(db.String(1000))
    available = db.Column(db.Integer())
    used = db.Column(db.Integer())


class AssetSystemInterface(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    asset_id = db.Column(GUID, db.ForeignKey('asset.id', ondelete="CASCADE"), nullable=False)
    device = db.Column(db.String(1000))
    macaddress = db.Column(db.String(1000))
    mtu = db.Column(db.Integer())
    active = db.Column(db.Boolean())


class Discovery(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(1000))
    discovery_method = db.Column(db.String(50))
    region_id = db.Column(GUID, db.ForeignKey('region.id'), nullable=True)
    status = db.Column(db.String(50), default='created')

    region = db.relationship("Region", foreign_keys=[region_id])


class DiscoveredAsset(db.Model):
    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    discovery_id = db.Column(GUID, db.ForeignKey('discovery.id', ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(1000))
    ip_address = db.Column(db.String(128))
    status = db.Column(db.String(50), default='new')

    discovery = db.relationship("Discovery", foreign_keys=[discovery_id])


def insert_default_abilities(*args, **kwargs):
    db.session.merge(Ability(id="fe4afeab515148b885964993b6081adb", name="organizations.list"))
    db.session.merge(Ability(id="9424c4b829a44bf4b537d27bcd6d769f", name="organizations.edit"))
    db.session.merge(Ability(id='c2fd2319e62e46cd98c4fafd912ef5e7', name='roles.edit'))
    db.session.merge(Ability(id='c2952f1411cd44bba128e811b32a2c5c', name='roles.list'))
    db.session.merge(Ability(id='54ad1d3d01184085af4cb48b42fd9eb0', name='users.edit'))
    db.session.merge(Ability(id='9fadeec875974bcdb3f362ae31954a1c', name='users.list'))
    db.session.merge(Ability(id='e4e7b07446dc4d16b9f2036a4eb966f3', name='regions.edit'))
    db.session.merge(Ability(id='70a5aff1e4ae4844977278e7d4f85ae1', name='regions.list'))
    db.session.merge(Ability(id='1ee1d47275eb4f9f8086de176f6898f9', name='configuration'))
    db.session.merge(Ability(id='34ad1d3d08184085af4cb48b42fd8eb0', name='ipam.edit'))
    db.session.merge(Ability(id='7fadeec875974bcdb3f367ae31954a0c', name='ipam.list'))
    db.session.merge(Ability(id='969e0c103445471886c15f5eb8f52ea1', name='password_manager.edit'))
    db.session.merge(Ability(id='969e0c103445471886c15f5eb8f52eac', name='password_manager.list'))
    db.session.merge(Ability(id='54ad1d3d08184085af4cb48b42fd8eb0', name='assets.edit'))
    db.session.merge(Ability(id='9fadeec875974bcdb3f367ae31954a0c', name='assets.list'))
    db.session.commit()


def insert_default_configurations(*args, **kwargs):
    db.session.merge(Configuration(id='071c34d70ffc414d9dbc525cf2a318ef', name='force_redirect_to_https', value='False'))
    db.session.merge(Configuration(id='4275cccd2ebf4ddaa70825a85b1f431d', name='mail_secure', value='False'))
    db.session.merge(Configuration(id='61fd39464e1e4c0e98b76be07c1ab762', name='default_language', value='English'))
    db.session.merge(Configuration(id='76c38a787bf6466ea054a2ebca658659', name='registration_confirmation', value='False'))
    db.session.merge(Configuration(id='f57aca01100c49baa489e7d7f560ea07', name='mail_host', value='localhost'))
    db.session.merge(Configuration(id='9043414b54b14f6eb8d0d1178c37a5d1', name='users_can_register', value='True'))
    db.session.merge(Configuration(id='c51e3a8bb9404614b0890a9f2bbb3dea', name='mail_port', value='25'))
    db.session.merge(Configuration(id='754027727d9e4db795e3b9269599ed46', name='mail_password', value=''))
    db.session.merge(Configuration(id='d0e88eccac8140ed9c7eacf743bb4af2', name='mail_username', value=''))
    db.session.merge(Configuration(id='a8639f8de0424d0f802b224f72f2d0d8', name='proxy_required', value='False'))
    db.session.merge(Configuration(id='070c20e3c0dc48aaaaf51bc132706af1', name='proxy_host', value='localhost'))
    db.session.merge(Configuration(id='1da6e95ca76c4f69bad317480e58ab1e', name='proxy_port', value='80'))
    db.session.merge(Configuration(id='9ccc6f9b95b24e73b161c6cd74912e89', name='sitename', value='LinuFy'))
    db.session.commit()


def create_tables():
    """Create Tables and populate certain ones"""
    db.create_all()
    if not exists('installed'):
        insert_default_abilities()
        insert_default_configurations()
        with open('installed', 'w') as f:
            f.write('installed')
