"""Fixture deliberadamente inseguro para probar las reglas Semgrep locales."""

import builtins
import json
import os
import os as sistema_operativo
import pickle
import pickle as serializacion
import platform
import subprocess
import subprocess as procesos
import tarfile
import tempfile
import tempfile as temporales
import tomllib
import urllib.request
import zipfile
from subprocess import Popen as abrir_proceso
from urllib.request import urlopen as abrir_url

import requests
import requests as cliente_http
import yaml
import yaml as yaml_alias


def casos_eval_exec(entrada_usuario):
    # ruleid: tramalia.python.eval-exec
    eval(entrada_usuario)
    # ruleid: tramalia.python.eval-exec
    eval(f"{entrada_usuario}")
    # ruleid: tramalia.python.eval-exec
    builtins.exec(entrada_usuario)
    # ok: tramalia.python.eval-exec
    eval("1 + 1")
    # ok: tramalia.python.eval-exec
    exec("resultado = 2")


def eval_sombreado_localmente(eval, entrada_usuario):
    # ok: tramalia.python.eval-exec
    return eval(entrada_usuario)


def casos_subprocess_shell(comando):
    # ruleid: tramalia.python.subprocess-shell
    subprocess.run(comando, shell=True, timeout=5)
    # ruleid: tramalia.python.subprocess-shell
    procesos.run(comando, shell=True, timeout=5)
    # ruleid: tramalia.python.subprocess-shell
    subprocess.call(comando, shell=True, timeout=5)
    # ruleid: tramalia.python.subprocess-shell
    subprocess.check_call(comando, shell=True, timeout=5)
    # ruleid: tramalia.python.subprocess-shell
    subprocess.check_output(comando, shell=True, timeout=5)
    # ruleid: tramalia.python.subprocess-shell
    proceso = subprocess.Popen(comando, shell=True)
    proceso.wait(timeout=5)
    # ok: tramalia.python.subprocess-shell
    subprocess.run(comando, shell=False, timeout=5)


def casos_sistema_shell(comando):
    # ruleid: tramalia.python.sistema-shell
    os.system(comando)
    # ruleid: tramalia.python.sistema-shell
    sistema_operativo.popen(comando)
    # ok: tramalia.python.sistema-shell
    platform.system()


def casos_run_sin_timeout(comando, ejecutor):
    # ruleid: tramalia.python.proceso-sin-timeout
    subprocess.run(comando)
    # ruleid: tramalia.python.proceso-sin-timeout
    procesos.run(comando, timeout=None)
    # ok: tramalia.python.proceso-sin-timeout
    subprocess.run(comando, timeout=5)
    # ok: tramalia.python.proceso-sin-timeout
    ejecutor.run(comando)


def popen_no_asignado(comando):
    # ruleid: tramalia.python.proceso-sin-timeout
    subprocess.Popen(comando)


def popen_encadenado(comando):
    # ruleid: tramalia.python.proceso-sin-timeout
    subprocess.Popen(comando).wait(timeout=5)


def popen_asignado_sin_espera(comando):
    # ruleid: tramalia.python.proceso-sin-timeout
    proceso = subprocess.Popen(comando)
    return proceso.pid


def popen_asignado_con_wait_sin_timeout(comando):
    # ruleid: tramalia.python.proceso-sin-timeout
    proceso = subprocess.Popen(comando)
    proceso.wait()


def popen_alias_con_communicate_sin_timeout(comando):
    # ruleid: tramalia.python.proceso-sin-timeout
    proceso = abrir_proceso(comando)
    proceso.communicate()


def popen_con_wait_none(comando):
    proceso = subprocess.Popen(comando)
    # ruleid: tramalia.python.proceso-sin-timeout
    proceso.wait(timeout=None)


def popen_con_communicate_none(comando):
    proceso = subprocess.Popen(comando)
    # ruleid: tramalia.python.proceso-sin-timeout
    proceso.communicate(timeout=None)


def popen_con_wait_acotado(comando):
    # ok: tramalia.python.proceso-sin-timeout
    proceso = subprocess.Popen(comando)
    proceso.wait(timeout=5)


def popen_con_communicate_acotado(comando):
    # ok: tramalia.python.proceso-sin-timeout
    proceso = procesos.Popen(comando)
    proceso.communicate(timeout=5)


def popen_con_watchdog_y_wait_local(comando):
    # Este flujo representa el helper real de installer.py.
    # ok: tramalia.python.proceso-sin-timeout
    proceso = subprocess.Popen(comando, stdout=subprocess.PIPE, text=True)
    salida = proceso.stdout
    if salida is not None:
        for _linea in iter(salida.readline, ""):
            pass
    proceso.wait(timeout=30)


def casos_pickle(datos):
    # ruleid: tramalia.python.pickle-inseguro
    pickle.loads(datos)
    # ruleid: tramalia.python.pickle-inseguro
    serializacion.load(datos)
    # ok: tramalia.python.pickle-inseguro
    json.loads(datos)
    # ok: tramalia.python.pickle-inseguro
    tomllib.loads(datos)


def casos_yaml(datos):
    # ruleid: tramalia.python.yaml-inseguro
    yaml.load(datos)
    # ruleid: tramalia.python.yaml-inseguro
    yaml_alias.load(datos, Loader=yaml_alias.Loader)
    # ruleid: tramalia.python.yaml-inseguro
    yaml.load(datos, Loader=yaml.FullLoader)
    # ruleid: tramalia.python.yaml-inseguro
    yaml.load(datos, yaml.FullLoader)
    # ok: tramalia.python.yaml-inseguro
    yaml.load(datos, Loader=yaml.SafeLoader)
    # ok: tramalia.python.yaml-inseguro
    yaml.load(datos, Loader=yaml.CSafeLoader)
    # ok: tramalia.python.yaml-inseguro
    yaml.load(datos, yaml.SafeLoader)
    # ok: tramalia.python.yaml-inseguro
    yaml.load(datos, yaml.CSafeLoader)
    # ok: tramalia.python.yaml-inseguro
    yaml.safe_load(datos)


def casos_mktemp(tmp_path_factory):
    # ruleid: tramalia.python.mktemp-inseguro
    tempfile.mktemp()
    # ruleid: tramalia.python.mktemp-inseguro
    temporales.mktemp(suffix=".txt")
    # ok: tramalia.python.mktemp-inseguro
    tmp_path_factory.mktemp("datos")


def casos_tls():
    # ruleid: tramalia.python.tls-sin-verificar
    requests.get("https://example.test", verify=False, timeout=5)
    # ruleid: tramalia.python.tls-sin-verificar
    cliente_http.post("https://example.test", verify=False, timeout=5)
    # ruleid: tramalia.python.tls-sin-verificar
    requests.request("GET", "https://example.test", verify=False, timeout=5)
    # ok: tramalia.python.tls-sin-verificar
    requests.get("https://example.test", verify=True, timeout=5)


def casos_red_sin_timeout():
    # ruleid: tramalia.python.red-sin-timeout
    requests.get("https://example.test")
    # ruleid: tramalia.python.red-sin-timeout
    cliente_http.post("https://example.test", timeout=None)
    # ruleid: tramalia.python.red-sin-timeout
    requests.request("GET", "https://example.test")
    # ruleid: tramalia.python.red-sin-timeout
    requests.request("GET", "https://example.test", timeout=None)
    # ruleid: tramalia.python.red-sin-timeout
    urllib.request.urlopen("https://example.test")
    # ruleid: tramalia.python.red-sin-timeout
    abrir_url("https://example.test", timeout=None)
    # ok: tramalia.python.red-sin-timeout
    requests.get("https://example.test", timeout=5)
    # ok: tramalia.python.red-sin-timeout
    urllib.request.urlopen("https://example.test", timeout=5)


def casos_sesion_requests():
    sesion_clase = requests.Session()
    # ruleid: tramalia.python.tls-sin-verificar
    sesion_clase.get("https://example.test", verify=False, timeout=5)
    # ruleid: tramalia.python.red-sin-timeout
    sesion_clase.request("GET", "https://example.test")
    # ok: tramalia.python.tls-sin-verificar
    # ok: tramalia.python.red-sin-timeout
    sesion_clase.get("https://example.test", verify=True, timeout=5)

    sesion_funcion = requests.session()
    # ruleid: tramalia.python.red-sin-timeout
    sesion_funcion.post("https://example.test", timeout=None)
    # ruleid: tramalia.python.tls-sin-verificar
    sesion_funcion.request("GET", "https://example.test", verify=False, timeout=5)
    # ok: tramalia.python.tls-sin-verificar
    # ok: tramalia.python.red-sin-timeout
    sesion_funcion.request("GET", "https://example.test", verify=True, timeout=5)


def extraer_tar_sin_frontera(ruta, destino):
    archivo = tarfile.open(ruta)
    # ruleid: tramalia.python.extraccion-insegura
    archivo.extractall(destino)


def extraer_zip_sin_frontera(ruta, destino):
    with zipfile.ZipFile(ruta) as archivo:
        # ruleid: tramalia.python.extraccion-insegura
        archivo.extractall(destino)


def extraer_tar_en_contexto_sin_frontera(ruta, destino):
    with tarfile.open(ruta) as archivo:
        # ruleid: tramalia.python.extraccion-insegura
        archivo.extractall(destino)


def extraer_zip_asignado_sin_frontera(ruta, destino):
    archivo = zipfile.ZipFile(ruta)
    # ruleid: tramalia.python.extraccion-insegura
    archivo.extractall(destino)


def extraer_con_constructor_encadenado(ruta, destino):
    # ruleid: tramalia.python.extraccion-insegura
    tarfile.open(ruta).extractall(destino)
    # ruleid: tramalia.python.extraccion-insegura
    zipfile.ZipFile(ruta).extractall(destino)


def extraer_con_objeto_propio(archivo, destino):
    # ok: tramalia.python.extraccion-insegura
    archivo.extractall(destino)


class ServidorFalso:
    def tool(self, *_argumentos, **_opciones):
        return decorador


def decorador(funcion):
    return funcion


servidor = ServidorFalso()


@servidor.tool()
def herramienta_sincrona():
    # ruleid: tramalia.python.mcp-stdout-directo
    print("dato sensible")


@decorador
@servidor.tool(nombre="asincrona")
async def herramienta_asincrona():
    # ruleid: tramalia.python.mcp-stdout-directo
    print("dato sensible")


@servidor.tool()
def herramienta_con_consola(_consola):
    # ok: tramalia.python.mcp-stdout-directo
    _consola.print("salida controlada")


def funcion_normal():
    # ok: tramalia.python.mcp-stdout-directo
    print("salida normal")
