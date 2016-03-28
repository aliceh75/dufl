# Default values for settings.yaml. This also defines the keys allowed in the settings file.
settings = {
     'git': '/usr/bin/git',
    'suspicious_names': {
        'id_rsa$': 'this looks like a private key'
    },
    'suspicous_content': {
        '-BEGIN .+ PRIVATE KEY-': 'this looks like a private key'
    }
}
