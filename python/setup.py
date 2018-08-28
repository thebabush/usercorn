import cffi


CDEF = r'''
extern "Python" void print_func(int);

// Defined in Go
typedef unsigned char byte;
typedef int opaque;
typedef unsigned int uint64;

extern void PDec(opaque addr);
extern char* _usercorn_getExe(opaque addr);
extern void _usercorn_setHookSysAdd(void (*)(int));
extern uint64 _Usercorn_Base(opaque);
extern uint64 _Usercorn_Entry(opaque);
extern opaque _Usercorn_DirectRead(opaque, uint64, uint64);

extern byte _array_byte_get(opaque, uint64);
extern int _array_len(opaque);

// Other stuff
void free(void *);
'''

SOURCE = r'''
typedef void (*callback_fcn)(int);

void call_callback_fcn(callback_fcn cb, int val) {
    cb(val);
}
'''

EMBEDDING_API = r'''
// typedef unsigned int opaque;

// Defined in Python
void call_python(opaque addr);
void on_init(opaque uc);
'''

INIT_CODE = r'''
from __future__ import print_function

from usercorn import _ffi, _lib


class Autofree(object):
    def __new__(cls, cp, *args, **kwargs):
        cp_ = cp
        if '_af_convert' in cls.__dict__:
            cp = cls._af_convert(cls, cp)
        self = super(Autofree, cls).__new__(cls, cp)
        self._pointer = cp_
        return self

    def __del__(self):
        _lib.free(self._pointer)
        p = super(Autofree, self)
        if '__del__' in p.__class__.__dict__:
            super(Autofree, self).__del__()


class String(Autofree, str):
    @staticmethod
    def _af_convert(cls, cp):
        return _ffi.string(cp)


@_ffi.def_extern()
def call_python(addr):
    print('call_python({})'.format(addr))


@_ffi.def_extern()
def print_func(arg):
    print("callback({})".format(arg))


@_ffi.def_extern()
def on_init(uc):
    exe = String(_lib._usercorn_getExe(uc))
    _lib._usercorn_setHookSysAdd(_lib.print_func)
    uc = Usercorn(uc)

    print("BASE:", hex(uc.base))
    print("EXE:", exe)
    print("ENTRY:", hex(uc.entry))
    print("READ:", uc.direct_read(uc.entry, 4))
    print(''.join(map(chr, uc.direct_read(0x400000, 4))))


class Autodec(object):
    def __init__(self, opaque):
        self._opaque = opaque

    def __del__(self):
        _lib.PDec(self._opaque)


class Array(Autodec):
    def __init__(self, opaque, getter=_lib._array_byte_get):
        Autodec.__init__(self, opaque)
        self._getter = getter

    def __getitem__(self, i):
        return self._getter(self._opaque, i)

    def __getslice__(self, *args):
        return [self[i] for i in range(*args)]

    def __iter__(self):
        return (self[i] for i in range(len(self)))

    def __len__(self):
        return _lib._array_len(self._opaque)

    def __str__(self):
        return '[' + ', '.join(str(self[i]) for i in range(len(self))) + ']'


class Usercorn(object):
    def __init__(self, native):
        self._native = native

    def __del__(self):
        _lib.PDec(self._native)

    @property
    def base(self):
        return _lib._Usercorn_Base(self._native)

    def direct_read(self, addr, size):
        return Array(_lib._Usercorn_DirectRead(self._native, addr, size))

    @property
    def entry(self):
        return _lib._Usercorn_Entry(self._native)
'''


def build_cffi():
    ffi = cffi.FFI()
    ffi.cdef(CDEF)
    ffi.set_source('_usercorn', SOURCE)
    ffi.embedding_api(EMBEDDING_API);
    ffi.embedding_init_code(INIT_CODE)
    return ffi


if __name__ == '__main__':
    ffi = build_cffi()
    ffi.emit_c_code('./python_binding.c')

