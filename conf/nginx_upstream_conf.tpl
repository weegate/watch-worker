upstream {+{UPSTREAM_NAME}+}#{+{UPSTREAM_TAG}+}{
▸   server {+{HOST:PORT}+} weight={+{WEIGHT}+} fail_timeout={+{FAIL_TIMEOUT}+} max_fails={+{MAX_FAILS}+} backup={+{BACKUP}+} down={+{DOWN}+};
}

