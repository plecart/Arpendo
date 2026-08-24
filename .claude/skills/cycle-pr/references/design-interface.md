# Concevoir des interfaces testables

De bonnes interfaces rendent le test naturel :

1. **Accepter les dépendances, ne pas les créer**

   ```typescript
   // Testable
   function processOrder(order, paymentGateway) {}

   // Difficile à tester
   function processOrder(order) {
     const gateway = new StripeGateway();
   }
   ```

2. **Renvoyer des résultats, éviter les effets de bord**

   ```typescript
   // Testable
   function calculateDiscount(cart): Discount {}

   // Difficile à tester
   function applyDiscount(cart): void {
     cart.total -= discount;
   }
   ```

3. **Petite surface**
   - Moins de méthodes = moins de tests nécessaires
   - Moins de paramètres = setup de test plus simple
