# TODO try this out and see if we can get it to work
# https://grok.com/share/bGVnYWN5_d1084241-d8c6-4827-a1a8-19bd8bc0672d
def auto_relationships(cls):
    """
    We’ll define a decorator auto_relationships that inspects the model’s fields, identifies foreign keys via the metadata, and adds the corresponding relationship fields:
    """

    for field_name, field in cls.__fields__.items():
        # Check if the field has a related_model in its extra metadata
        related_model = field.field_info.extra.get("related_model")
        if related_model:
            # Derive the relationship field name by removing '_id'
            relationship_field_name = field_name.replace("_id", "")
            # Set back_populates to the pluralized lowercase class name
            back_populates = cls.__name__.lower() + "s"
            # Create the relationship descriptor
            relationship = Relationship(back_populates=back_populates)
            # Add the type annotation if not already present
            if relationship_field_name not in cls.__annotations__:
                cls.__annotations__[relationship_field_name] = related_model
            # Set the attribute on the class
            setattr(cls, relationship_field_name, relationship)
    return cls
