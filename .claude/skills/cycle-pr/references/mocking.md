# Quand mocker

Mocker uniquement aux **frontières du système** :

- APIs externes (paiement, e-mail, etc.)
- Bases de données (parfois — préférer une base de test)
- Temps / aléatoire
- Système de fichiers (parfois)

Ne pas mocker :

- Ses propres classes / modules
- Les collaborateurs internes
- Tout ce qu'on contrôle

## Concevoir pour la mockabilité

Aux frontières du système, concevoir des interfaces faciles à mocker :

**1. Injection de dépendances**

Passer les dépendances externes plutôt que les créer en interne :

```typescript
// Facile à mocker
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// Difficile à mocker
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**2. Préférer des interfaces façon SDK aux fetchers génériques**

Créer une fonction spécifique par opération externe plutôt qu'une fonction générique à logique
conditionnelle :

```typescript
// BON : chaque fonction est mockable indépendamment
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// MAUVAIS : mocker exige une logique conditionnelle dans le mock
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

L'approche SDK signifie :
- Chaque mock renvoie une forme spécifique
- Aucune logique conditionnelle dans le setup de test
- On voit plus facilement quels endpoints un test exerce
- Sûreté de typage par endpoint
