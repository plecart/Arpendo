# Bons et mauvais tests

> Les exemples de cette page et des autres références de `cycle-pr` sont écrits en TypeScript par
> concision. **Les principes sont indépendants du langage** — transposer aux idiomes de la stack du
> projet (celle déclarée dans `.claude/pipeline.config.md`), pas introduire TypeScript.

## Bons tests

**Style intégration** : tester à travers de vraies interfaces, pas des mocks de parties internes.

```typescript
// BON : teste un comportement observable
test("un utilisateur peut payer avec un panier valide", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

Caractéristiques :

- Teste le comportement qui intéresse les utilisateurs/appelants
- Utilise l'API publique uniquement
- Survit aux refactors internes
- Décrit le QUOI, pas le COMMENT
- Une assertion logique par test

## Mauvais tests

**Tests de détails d'implémentation** : couplés à la structure interne.

```typescript
// MAUVAIS : teste des détails d'implémentation
test("checkout appelle paymentService.process", async () => {
  const mockPayment = jest.mock(paymentService);
  await checkout(cart, payment);
  expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
});
```

Signaux d'alerte :

- Mocker des collaborateurs internes
- Tester des méthodes privées
- Asserter sur le nombre/l'ordre des appels
- Le test casse lors d'un refactor sans changement de comportement
- Le nom du test décrit le COMMENT, pas le QUOI
- Vérifier par un moyen externe au lieu de l'interface

```typescript
// MAUVAIS : contourne l'interface pour vérifier
test("createUser enregistre en base", async () => {
  await createUser({ name: "Alice" });
  const row = await db.query("SELECT * FROM users WHERE name = ?", ["Alice"]);
  expect(row).toBeDefined();
});

// BON : vérifie à travers l'interface
test("createUser rend l'utilisateur récupérable", async () => {
  const user = await createUser({ name: "Alice" });
  const retrieved = await getUser(user.id);
  expect(retrieved.name).toBe("Alice");
});
```
