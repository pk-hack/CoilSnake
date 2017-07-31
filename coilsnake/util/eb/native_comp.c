#include <stdio.h>
#include <string.h>
#include <Python.h>

#include "exhal/compress.h"

static PyObject* comp(PyObject* self, PyObject* args) {
	PyObject *list, *clist, *o;
        size_t size, i, csize;
	long n;
	uint8_t *udata, *buffer;

	if (!PyArg_ParseTuple(args, "O", &list))
		return NULL;

	if (!PyList_Check(list))
		return PyErr_Format(PyExc_TypeError, "list of numbers expected ('%s' given)", list->ob_type->tp_name), NULL;

	size = (size_t) PyList_Size(list);

	if (size < 1)
		return PyErr_Format(PyExc_TypeError, "got empty list"), NULL;

	udata = (uint8_t*) malloc(sizeof(uint8_t) * size);

	for (i=0; i < size; ++i) {
		o = PyList_GetItem(list, i);
		if (!PyLong_Check(o)) {
                        free(udata);
			return PyErr_Format(PyExc_TypeError, "list of ints expected ('%s') given", o->ob_type->tp_name), NULL;
                }
                n = PyLong_AsLong(o);
		if (n == -1 && PyErr_Occurred()) {
                        free(udata);
			return NULL;
                }
		if (n < 0) {
                        free(udata);
			return PyErr_Format(PyExc_TypeError, "list of positive ints expected (negative found)"), NULL;
                }
                udata[i] = (uint8_t) n;
	}

	// Allocate a buffer
	buffer = (uint8_t*) malloc(sizeof(uint8_t) * (size + 1));
	csize = pack(udata, size, buffer, 1);
	free(udata);

	clist = PyList_New(csize);
	for (i=0; i<csize; ++i) {
		o = PyLong_FromLong((long) buffer[i]);
		PyList_SetItem(clist, i, o);
	}
	free(buffer);
	return clist;
}

// Given a reference to a Block object, returns a PyByteArray containing its data
// Caches the data from the most recent Block object passed in in order to reduce allocations and marshalling costs
PyObject* get_rom_bytes(PyObject* rom) {
        static PyObject *s_cachedRomArr, *s_cachedRomByteArr;
        PyObject *romArr, *romByteArr;
        Py_ssize_t size;

	romArr = PyObject_GetAttr(rom, PyUnicode_FromString("data"));
        if (!romArr)
                return NULL;
        
        // If rom.data array reference hasn't changed, return the cached byte buffer
        if (romArr == s_cachedRomArr) {
                Py_DECREF(romArr);
                return s_cachedRomByteArr;
        }

	romByteArr = PyByteArray_FromObject(romArr);
        if (!romByteArr)
                return NULL;

        if (!PyByteArray_Check(romByteArr))
                return PyErr_Format(PyExc_TypeError, "bytearray of numbers expected ('%s') given", romArr->ob_type->tp_name);

        size = PyByteArray_Size(romByteArr);

        if (size < 1)
                return PyErr_Format(PyExc_TypeError, "rom's data attribute was empty");

        // We are replacing the cached references, so release them before we do
        Py_XDECREF(s_cachedRomArr);
        Py_XDECREF(s_cachedRomByteArr);
        
        // Because this reference to the array is cached, there will always be an extra reference
        // to the rom's data until the program ends
        s_cachedRomArr = romArr;
        s_cachedRomByteArr = romByteArr;
        
        return romByteArr;
}

static PyObject* decomp(PyObject* self, PyObject* args) {
        PyObject *rom, *ulist, *o, *romByteArr;
	int addr;
        size_t new_size, i;
	uint8_t *romBuffer, *buffer;

        if (!PyArg_ParseTuple(args, "Oi", &rom, &addr))
                return NULL;

        romByteArr = get_rom_bytes(rom);
        if (!romByteArr)
                return NULL;

        romBuffer = (uint8_t*) PyByteArray_AS_STRING(romByteArr);

        // Allocate a buffer
        buffer = (uint8_t*) malloc(sizeof(uint8_t) * 65536);
        new_size = unpack(romBuffer + addr, buffer);

        ulist = PyList_New(new_size);
        for (i=0; i<new_size; ++i) {
                o = PyLong_FromLong((long) buffer[i]);
                PyList_SetItem(ulist, i, o);
        }
        free(buffer);
        return ulist;
}

static PyMethodDef native_comp_methods[] = {
	{"comp", comp, METH_VARARGS, "C implementation of EB's comp()"},
	{"decomp", decomp, METH_VARARGS, "C implementation of EB's decomp()"},
	{NULL, NULL, 0, NULL}
};

struct module_state {
    PyObject *error;
};

#define GETSTATE(m) ((struct module_state*)PyModule_GetState(m))

static int native_comp_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int native_comp_clear(PyObject *m) {
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}

static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "native_comp",
        NULL,
        sizeof(struct module_state),
        native_comp_methods,
        NULL,
        native_comp_traverse,
        native_comp_clear,
        NULL
};

PyMODINIT_FUNC
PyInit_native_comp(void)
{
	PyObject *module = PyModule_Create(&moduledef);
        return module;
}
