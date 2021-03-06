# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: grpc_midi.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='grpc_midi.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=b'\n\x0fgrpc_midi.proto\"\x15\n\x05Sysex\x12\x0c\n\x04\x64\x61ta\x18\x01 \x01(\x0c\"\x07\n\x05\x45mpty2F\n\x04Midi\x12 \n\x08MidiChat\x12\x06.Empty\x1a\x06.Sysex\"\x00(\x01\x30\x01\x12\x1c\n\x08SendMidi\x12\x06.Sysex\x1a\x06.Empty\"\x00\x62\x06proto3'
)




_SYSEX = _descriptor.Descriptor(
  name='Sysex',
  full_name='Sysex',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='data', full_name='Sysex.data', index=0,
      number=1, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=b"",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=19,
  serialized_end=40,
)


_EMPTY = _descriptor.Descriptor(
  name='Empty',
  full_name='Empty',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=42,
  serialized_end=49,
)

DESCRIPTOR.message_types_by_name['Sysex'] = _SYSEX
DESCRIPTOR.message_types_by_name['Empty'] = _EMPTY
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Sysex = _reflection.GeneratedProtocolMessageType('Sysex', (_message.Message,), {
  'DESCRIPTOR' : _SYSEX,
  '__module__' : 'grpc_midi_pb2'
  # @@protoc_insertion_point(class_scope:Sysex)
  })
_sym_db.RegisterMessage(Sysex)

Empty = _reflection.GeneratedProtocolMessageType('Empty', (_message.Message,), {
  'DESCRIPTOR' : _EMPTY,
  '__module__' : 'grpc_midi_pb2'
  # @@protoc_insertion_point(class_scope:Empty)
  })
_sym_db.RegisterMessage(Empty)



_MIDI = _descriptor.ServiceDescriptor(
  name='Midi',
  full_name='Midi',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=51,
  serialized_end=121,
  methods=[
  _descriptor.MethodDescriptor(
    name='MidiChat',
    full_name='Midi.MidiChat',
    index=0,
    containing_service=None,
    input_type=_EMPTY,
    output_type=_SYSEX,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='SendMidi',
    full_name='Midi.SendMidi',
    index=1,
    containing_service=None,
    input_type=_SYSEX,
    output_type=_EMPTY,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_MIDI)

DESCRIPTOR.services_by_name['Midi'] = _MIDI

# @@protoc_insertion_point(module_scope)
