# Sito di Quanto Manca

Le pagine HTML si generano: non modificarle a mano.

- `holidays.py`: feste, date e testi. Per una nuova festa aggiungi una voce e le sue icone in `assets/icons`.
- `build_site.py`: modelli delle pagine. In alto ci sono `APP_STORE_URL` (da inserire quando l'app è pubblicata) e l'email di supporto.
- `make_images.swift`: anteprime di condivisione in `assets/og` (solo su Mac, dal progetto completo).
- Stile e animazioni: `assets/site.css` e `assets/site.js`.

Dalla cartella `Website`:

```bash
python3 _build/build_site.py
```

```bash
swift _build/make_images.swift
```

Su GitHub il workflow `.github/workflows/aggiorna-date.yml` rigenera le pagine ogni notte.
