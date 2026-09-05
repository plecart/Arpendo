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

4. **Placer la couture là où il reste un objet inerte en dessous**

   Un paramètre injectable dont le défaut est une implémentation réelle
   (`initialiser = _initialiserReel`) laisse tout ce qui est sous la couture hors de portée des
   tests — et c'est là que logent les réglages qui touchent la plateforme, dont ceux de sécurité.
   Placer la couture, c'est décider ce qu'on renonce à prouver : extraire la configuration en
   fonction pure prenant l'objet d'options, que le test instancie sans réseau, plutôt qu'hériter
   de la première forme qui rendait le test facile.
