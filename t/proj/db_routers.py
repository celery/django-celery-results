class AlwaysSecondaryDbRouter:
    connection_name = "secondary"

    def db_for_read(self, model, **hints):
        """
        Route read always for the specified connection
        """
        return self.connection_name

    def db_for_write(self, model, **hints):
        """
        Route write always for the specified connection
        """
        return self.connection_name

    def allow_relation(self, obj1, obj2, **hints):
        """
        Router have no opinion here
        """
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Router have no opinion here
        """
        return None
