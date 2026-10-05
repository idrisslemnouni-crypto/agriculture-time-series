# Préparation entretien — séries temporelles

Problème : humidité volumique à 10 cm, horizons un et sept jours, NOAA Missouri. Origine quotidienne avec historique observé, backtests 2021/2022 puis test 2023/2024. Baselines persistance et saison ; modèles Ridge et RF. Les chiffres exacts figurent dans reports/metrics.json, en m³/m³.

1. **Pourquoi un split temporel ?** Pour reproduire la direction passée vers futur et éviter le mélange aléatoire des voisins temporels.
2. **Pourquoi purger à sept jours ?** Des cibles de janvier pourraient apparaître dans les lignes d'origine décembre.
3. **La météo future est-elle connue ?** Non ; seules les observations jusqu'à l'origine entrent dans le modèle.
4. **Pourquoi des prévisions directes ?** Un modèle par horizon évite de présenter une récursion comme une mesure observée.
5. **Pourquoi la station Missouri ?** Iowa avait un trou de mesures rendant la validation 2022 à sept jours impossible ; sélection selon couverture, pas score test.
6. **Pourquoi garder RF à J+1 si Ridge gagne un peu au test ?** Le choix est fixé sur validation ; rechoisir sur test le contaminerait.
7. **Pourquoi RMSE et MAE peuvent diverger ?** RMSE pondère davantage les grandes erreurs ; à sept jours le compromis observé est différent.
8. **Les intervalles garantissent-ils 90% ?** Non : erreurs historiques avec autocorrélation et drift, couverture et largeur mesurées seulement.
9. **Pourquoi pas LSTM ?** Petit échantillon et baseline forte ; la complexité doit être justifiée par un nouveau gain validé.
10. **Prochaine amélioration ?** Nouveaux sites/période indépendante, disponibilité réelle des mesures, météo réellement prévue et uncertainty par blocs.

Limites : une station, horizon superficiel et mesures manquantes. Assistance IA déclarée ; refaire le calcul d'un fold et d'une erreur avant de défendre le projet.
