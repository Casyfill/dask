import numpy as np
import pytest

import dask.array as da
from dask.sizeof import sizeof
from dask.array.utils import assert_eq

cupy = pytest.importorskip('cupy')


functions = [
    lambda x: x,
    lambda x: da.expm1(x),
    lambda x: 2 * x,
    lambda x: x / 2,
    lambda x: x**2,
    lambda x: x + x,
    lambda x: x * x,
    lambda x: x[0],
    lambda x: x[:, 1],
    lambda x: x[:1, None, 1:3],
    lambda x: x.T,
    lambda x: da.transpose(x, (1, 2, 0)),
    lambda x: x.sum(),
    pytest.param(lambda x: x.dot(np.arange(x.shape[-1])),
                 marks=pytest.mark.xfail(reason='cupy.dot(numpy) fails')),
    pytest.param(lambda x: x.dot(np.eye(x.shape[-1])),
                 marks=pytest.mark.xfail(reason='cupy.dot(numpy) fails')),
    pytest.param(lambda x: da.tensordot(x, np.ones(x.shape[:2]), axes=[(0, 1), (0, 1)]),
                 marks=pytest.mark.xfail(reason='cupy.dot(numpy) fails')),
    lambda x: x.sum(axis=0),
    lambda x: x.max(axis=0),
    lambda x: x.sum(axis=(1, 2)),
    lambda x: x.astype(np.complex128),
    lambda x: x.map_blocks(lambda x: x * 2),
    pytest.param(lambda x: x.round(1),
                 marks=pytest.mark.xfail(reason="cupy doesn't support round")),
    lambda x: x.reshape((x.shape[0] * x.shape[1], x.shape[2])),
    lambda x: abs(x),
    lambda x: x > 0.5,
    lambda x: x.rechunk((4, 4, 4)),
    lambda x: x.rechunk((2, 2, 1)),
    pytest.param(lambda x: da.einsum("ijk,ijk", x, x),
                 marks=pytest.mark.xfail(
                     reason='depends on resolution of https://github.com/numpy/numpy/issues/12974')),
    lambda x: np.isreal(x),
    lambda x: np.iscomplex(x),
    lambda x: np.isneginf(x),
    lambda x: np.isposinf(x),
    lambda x: np.real(x),
    lambda x: np.imag(x),
    lambda x: np.fix(x),
    lambda x: np.i0(x.reshape((24,))),
    lambda x: np.sinc(x),
    lambda x: np.nan_to_num(x),
]


@pytest.mark.parametrize('func', functions)
def test_basic(func):
    c = cupy.random.random((2, 3, 4))
    n = c.get()
    dc = da.from_array(c, chunks=(1, 2, 2), asarray=False)
    dn = da.from_array(n, chunks=(1, 2, 2))

    ddc = func(dc)
    ddn = func(dn)

    assert_eq(ddc, ddn)

    if ddc.shape:
        result = ddc.compute(scheduler='single-threaded')
        assert isinstance(result, cupy.ndarray)


@pytest.mark.parametrize('dtype', ['f4', 'f8'])
def test_sizeof(dtype):
    c = cupy.random.random((2, 3, 4), dtype=dtype)

    assert sizeof(c) == c.nbytes
