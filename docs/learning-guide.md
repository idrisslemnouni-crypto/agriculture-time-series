# Comprendre les prévisions

Une prévision à J+7 se construit avec les informations connues à J. La pluie réellement observée à J+7 serait une fuite. Ici les entrées sont les mesures jusqu'au jour d'origine, les valeurs retardées et les moyennes historiques. De nouvelles observations sont disponibles à chaque origine quotidienne ; cela ne simule pas une saison entière sans mises à jour.

Reconstituer le calendrier avant shift évite de confondre sept lignes et sept jours. Les cibles manquantes sont exclues, jamais imputées. La station initiale Iowa ne permettait pas le backtest 2022 à sept jours. Choisir Missouri pour sa couverture train/validation est une décision de qualité des données ; il ne faut pas choisir le site donnant le meilleur score test. La deuxième moitié de 2024 est incomplète et reste visible comme vide.

Les backtests élargissent le train puis évaluent une année future. Il faut purger par date de cible : une ligne d'origine en décembre avec cible en janvier ne doit pas entraîner le modèle du test janvier. Imputation et normalisation restent dans chaque fold. Le modèle choisi est ensuite figé sur le test futur ; un autre modèle légèrement meilleur sur ce test ne le remplace pas.

La persistance est une baseline forte car le sol évolue lentement. La climatologie décrit la saison habituelle, Ridge un compromis linéaire régularisé, RF des interactions locales. À J+7, Ridge améliore un peu RMSE mais dégrade MAE : les grosses erreurs et les erreurs typiques sont pondérées différemment. Un score ne résume pas toute l'utilité.

Le ruban utilise les erreurs historiques de validation. La dépendance temporelle invalide une promesse automatique de couverture « conformale ». Nous mesurons la couverture réellement obtenue et sa largeur. Un intervalle large peut couvrir beaucoup sans être très utile. LSTM n'est pas nécessaire pour démontrer la méthodologie sur quelques milliers de lignes.

À apprendre : dessiner une frontière de fold pour horizon 7, vérifier les dates d'une moyenne mobile, recalculer RMSE depuis les prédictions et expliquer pourquoi un intervalle à 95% de couverture observée n'est pas une garantie pour demain. Une prochaine étude doit utiliser une période nouvelle et mesurer la disponibilité opérationnelle des capteurs.
