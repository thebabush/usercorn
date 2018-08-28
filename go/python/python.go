package python

/*
#cgo pkg-config: python2
#cgo LDFLAGS: -L../../ -lpython_binding

#include <stdlib.h>

typedef int opaque;

void call_python(opaque addr);
void on_init(opaque cpu);

// Callback test
typedef void (*callback_fcn)(int);
void call_callback_fcn(callback_fcn cb, int arg);
*/
import "C"

import (
	"fmt"
	"reflect"

	"github.com/lunixbochs/usercorn/go/models"
)

type Opaque = C.int
type PValue = interface{}

type PRef struct {
	counter uint
	value   *PValue
}

var ptrs = map[Opaque]PRef{}
var nextAddr Opaque = 0

func GetOpaque(addr Opaque) *PValue {
	if val, ok := ptrs[addr]; ok {
		return val.value
	}
	panic(fmt.Sprintf("Invalid opaque address: %v", addr))
}

func MkOpaque(value PValue) Opaque {
	addr := nextAddr
	if _, exists := ptrs[addr]; exists {
		panic(fmt.Sprintf("Value is already opaque: %v", value))
	}
	ptrs[addr] = PRef{1, &value}
	nextAddr++
	return addr
}

//export PDec
func PDec(addr Opaque) {
	if val, exists := ptrs[addr]; exists {
		if val.counter > 0 {
			val.counter--
		}
		if val.counter == 0 {
			delete(ptrs, addr)
		}
	} else {
		panic(fmt.Sprintf("PDec received a non-existing address: %d", addr))
	}
}

//export PInc
func PInc(addr Opaque) {
	if val, exists := ptrs[addr]; exists {
		val.counter++
	} else {
		panic(fmt.Sprintf("PInc received a non-existing address: %d", addr))
	}
}

//export _usercorn_getExe
func _usercorn_getExe(addr Opaque) *C.char {
	v := (*GetOpaque(addr)).(models.Usercorn)
	return C.CString(v.Exe())
}

//export _Usercorn_Base
func _Usercorn_Base(u Opaque) uint64 {
	v := (*GetOpaque(u)).(models.Usercorn)
	return v.Base()
}

//export _Usercorn_Entry
func _Usercorn_Entry(u Opaque) uint64 {
	v := (*GetOpaque(u)).(models.Usercorn)
	return v.Entry()
}

//export _Usercorn_DirectRead
func _Usercorn_DirectRead(u Opaque, addr, size uint64) Opaque {
	//func _Usercorn_DirectRead(u Opaque, addr, read *uint64, size uint64) *void {
	fmt.Println(u, addr, size)
	v := (*GetOpaque(u)).(models.Usercorn)
	data, err := v.DirectRead(addr, size)
	if err == nil {
		return MkOpaque(data)
	} else {
		return -1
	}

	//read = len(data)
	//return unsafe.Pointer(
}

//export _usercorn_setHookSysAdd
func _usercorn_setHookSysAdd(fn C.callback_fcn) {
	C.call_callback_fcn(fn, 666)
}

//export _array_byte_get
func _array_byte_get(o Opaque, elem uint64) byte {
	v := (*GetOpaque(o)).([]byte)
	return v[elem]
}

//export _array_len
func _array_len(o Opaque) int {
	return reflect.ValueOf(*GetOpaque(o)).Len()
}

func ExecScript(usercorn models.Usercorn, cmd string) int {
	Opaque := MkOpaque(usercorn)
	C.on_init(Opaque)
	C.call_python(0)
	fmt.Println("===============================================\n\n")
	return 0
}
