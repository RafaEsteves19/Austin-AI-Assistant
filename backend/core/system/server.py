import threading


_servidor = None


def registrar_servidor(
    servidor
):

    global _servidor

    _servidor = servidor


def solicitar_shutdown():

    if _servidor is None:

        return False

    _servidor.should_exit = True

    return True