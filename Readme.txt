cleaner_md.py Description:

Python script named cleaner_md.py and processed all the Manuelita content files. Here's what was accomplished:

Script Features:
The cleaner_md.py script effectively removes:

1. Line numbers (e.g., "1|", "123|")
2. Image references ![alt](url) 
3. Markdown links - converts [text](url) to just text
4. Standalone URLs (http/https links)
5. WordPress toolbar section - including "Ir a la barra de herramientas" and related menu items
6. Social sharing buttons (Facebook, Twitter, LinkedIn, Instagram)
7. Navigation elements (×, Cerrar, Volver a, etc.)
8. Generic action words ("Leer más", "Conoce más", "Ver todas las noticias", etc.)
9. Excessive whitespace and empty lines
10. Special characters and symbols on standalone lines
11. WordPress menu items (WordPress.org, Documentación, etc.)

Results:
•  ✅ Successfully processed 39 files
•  ✅ Created cleaned_manuelita_content directory
•  ✅ All files cleaned and saved with same filenames
•  ✅ Preserved valuable content while removing navigation clutter