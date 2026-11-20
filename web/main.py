from pyscript import document

import hexxle.core  # noqa: F401

document.querySelector('#message').innerText = 'core ok'
document.documentElement.dataset.ready = '1'
