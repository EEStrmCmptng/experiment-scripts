# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: eflinkrpc.proto
# Protobuf Python Version: 5.26.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0f\x65\x66linkrpc.proto\"/\n\x0eUtilityMessage\x12\x0e\n\x06srcrps\x18\x01 \x01(\x02\x12\r\n\x05power\x18\x02 \x01(\x02\"\x1d\n\nUtilityAck\x12\x0f\n\x07retcode\x18\x01 \x01(\x05\x32\x44\n\x10UtilityMessaging\x12\x30\n\x0ePublishUtility\x12\x0f.UtilityMessage\x1a\x0b.UtilityAck\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'eflinkrpc_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_UTILITYMESSAGE']._serialized_start=19
  _globals['_UTILITYMESSAGE']._serialized_end=66
  _globals['_UTILITYACK']._serialized_start=68
  _globals['_UTILITYACK']._serialized_end=97
  _globals['_UTILITYMESSAGING']._serialized_start=99
  _globals['_UTILITYMESSAGING']._serialized_end=167
# @@protoc_insertion_point(module_scope)
