# Modules profonds

D'après « A Philosophy of Software Design » :

**Module profond** = petite interface + beaucoup d'implémentation

```
┌─────────────────────┐
│   Petite interface  │  ← Peu de méthodes, params simples
├─────────────────────┤
│                     │
│                     │
│ Implémentation      │  ← Logique complexe cachée
│ profonde            │
│                     │
└─────────────────────┘
```

**Module superficiel** = grande interface + peu d'implémentation (à éviter)

```
┌─────────────────────────────────┐
│        Grande interface         │  ← Beaucoup de méthodes, params complexes
├─────────────────────────────────┤
│  Implémentation fine            │  ← Ne fait que passer-plat
└─────────────────────────────────┘
```

En concevant une interface, se demander :

- Puis-je réduire le nombre de méthodes ?
- Puis-je simplifier les paramètres ?
- Puis-je cacher davantage de complexité à l'intérieur ?
