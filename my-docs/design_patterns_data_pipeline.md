# Design Patterns utilisés dans le Data Pipeline

Ce document explique les quatre concepts principaux utilisés dans notre
architecture de Data Pipeline :

1.  **Pipeline**
2.  **Strategy**
3.  **Factory**
4.  **Registry**

L'objectif est de comprendre **pourquoi** nous utilisons ces concepts et
**quel rôle chacun joue** dans le projet.

------------------------------------------------------------------------

## 1. Vue d'ensemble

Notre pipeline de traitement des données suit cette logique :

``` text
Input files
    │
    ▼
┌──────────┐
│  Load    │
└────┬─────┘
     ▼
┌──────────┐
│  Clean   │
└────┬─────┘
     ▼
┌──────────┐
│ Validate │
└────┬─────┘
     ▼
┌──────────┐
│  Derive  │
└────┬─────┘
     ▼
┌──────────┐
│   Save   │
└──────────┘
```

Pour les fichiers CSV et Markdown, l'ordre général reste le même :

``` text
Load → Clean → Validate → Derive → Save
```

Mais **la manière de réaliser chaque étape change** selon le type de
données.

Par exemple :

``` text
CSV
 ├── CsvLoadingStrategy
 ├── CsvCleaningStrategy
 ├── CsvValidationStrategy
 ├── CsvDeriveStrategy
 └── CsvSaveStrategy

Markdown
 ├── MarkdownLoadingStrategy
 ├── MarkdownCleaningStrategy
 ├── MarkdownValidationStrategy
 ├── MarkdownDeriveStrategy
 └── MarkdownSaveStrategy
```

C'est précisément là que les Design Patterns deviennent utiles.

------------------------------------------------------------------------

# 2. Pipeline Pattern

## Définition

Le **Pipeline Pattern** sert à organiser plusieurs étapes de traitement
dans un ordre précis.

La question à laquelle il répond est :

> **"Dans quel ordre les opérations doivent-elles être exécutées ?"**

Dans notre projet :

``` text
Load
  ↓
Clean
  ↓
Validate
  ↓
Derive
  ↓
Save
```

Le Pipeline ne se préoccupe pas de savoir **comment** le nettoyage
fonctionne.

Il sait seulement :

> "J'ai plusieurs stages et je dois les exécuter dans cet ordre."

------------------------------------------------------------------------

## Exemple simple

Imaginons une usine :

``` text
Matière première
      ↓
Nettoyage
      ↓
Transformation
      ↓
Contrôle qualité
      ↓
Produit final
```

Chaque étape reçoit le résultat de l'étape précédente.

C'est exactement le principe de notre Data Pipeline.

------------------------------------------------------------------------

## Exemple en Python

Notre classe `Pipeline` peut être très simple :

``` python
class Pipeline:

    def __init__(self, stages):
        self.stages = stages

    def run(self, data):
        for stage in self.stages:
            data = stage.run(data)

        return data
```

On peut ensuite construire :

``` python
pipeline = Pipeline(
    stages=[
        LoadStage(...),
        CleanStage(...),
        ValidateStage(...),
        DeriveStage(...),
        SaveStage(...),
    ]
)
```

Puis :

``` python
pipeline.run(data)
```

------------------------------------------------------------------------

## Ce que le Pipeline fait

Le Pipeline :

-   organise les étapes ;
-   définit leur ordre ;
-   transmet les données d'une étape à l'autre ;
-   reste indépendant du type de données.

Il ne doit pas contenir :

``` python
if csv:
    ...
elif markdown:
    ...
```

Le Pipeline doit rester générique.

------------------------------------------------------------------------

# 3. Strategy Pattern

## Définition

Le **Strategy Pattern** permet de définir plusieurs façons de réaliser
une même opération et de choisir celle dont on a besoin.

La question à laquelle il répond est :

> **"Comment réaliser cette opération ?"**

Dans notre projet, le problème est simple.

Nous avons une étape :

``` text
Clean
```

Mais CSV et Markdown ne se nettoient pas de la même manière.

Donc nous avons :

``` text
CleaningStrategy
       │
       ├── CsvCleaningStrategy
       │
       └── MarkdownCleaningStrategy
```

------------------------------------------------------------------------

## Exemple simple

Supposons qu'on veuille calculer un prix.

On peut avoir :

``` text
PaymentStrategy
       │
       ├── CreditCardStrategy
       ├── PayPalStrategy
       └── BankTransferStrategy
```

L'opération générale est :

``` text
Pay
```

Mais la manière de payer change.

C'est exactement le même principe dans notre projet.

------------------------------------------------------------------------

## Exemple dans notre projet

Pour le nettoyage :

``` python
class CleaningStrategy(ABC):

    @abstractmethod
    def clean(self, data):
        pass
```

Puis :

``` python
class CsvCleaningStrategy(CleaningStrategy):

    def clean(self, data):
        # nettoyage CSV
        ...
```

et :

``` python
class MarkdownCleaningStrategy(CleaningStrategy):

    def clean(self, data):
        # nettoyage Markdown
        ...
```

------------------------------------------------------------------------

## Pourquoi Strategy est utile ?

Sans Strategy, on pourrait écrire :

``` python
class CleanStage:

    def run(self, data):

        if data_is_csv:
            # nettoyage CSV

        elif data_is_markdown:
            # nettoyage Markdown
```

Cela fonctionne au début, mais la classe devient rapidement compliquée.

Avec Strategy :

``` text
CleanStage
    │
    └── CleaningStrategy
            │
            ├── CSV
            └── Markdown
```

`CleanStage` n'a pas besoin de connaître les détails.

Il fait simplement :

``` python
self.strategy.clean(data)
```

------------------------------------------------------------------------

# 4. Stage + Strategy

C'est une distinction très importante dans notre architecture.

## Stage

Le **Stage** représente une étape du pipeline.

Exemples :

``` text
LoadStage
CleanStage
ValidateStage
DeriveStage
SaveStage
```

## Strategy

La **Strategy** représente la manière d'effectuer cette étape.

Exemples :

``` text
CsvLoadingStrategy
MarkdownLoadingStrategy

CsvCleaningStrategy
MarkdownCleaningStrategy

CsvValidationStrategy
MarkdownValidationStrategy
```

On peut visualiser cela ainsi :

``` text
Pipeline
   │
   ├── LoadStage
   │      └── LoadingStrategy
   │             ├── CSV
   │             └── Markdown
   │
   ├── CleanStage
   │      └── CleaningStrategy
   │             ├── CSV
   │             └── Markdown
   │
   ├── ValidateStage
   │      └── ValidationStrategy
   │             ├── CSV
   │             └── Markdown
   │
   ├── DeriveStage
   │      └── DeriveStrategy
   │             ├── CSV
   │             └── Markdown
   │
   └── SaveStage
          └── SaveStrategy
                 ├── CSV
                 └── Markdown
```

### Phrase à retenir

> **Stage = quelle étape ?**
>
> **Strategy = comment réaliser cette étape ?**

------------------------------------------------------------------------

# 5. Factory Pattern

## Définition

Le **Factory Pattern** sert à créer les bons objets.

La question à laquelle il répond est :

> **"Quel objet dois-je créer ?"**

Par exemple, si notre programme détecte :

``` text
CSV
```

il doit créer :

``` python
CsvCleaningStrategy()
```

Si le programme détecte :

``` text
Markdown
```

il doit créer :

``` python
MarkdownCleaningStrategy()
```

La Factory centralise cette logique de création.

------------------------------------------------------------------------

## Exemple simple

Sans Factory :

``` python
if data_type == "csv":
    strategy = CsvCleaningStrategy()

elif data_type == "markdown":
    strategy = MarkdownCleaningStrategy()
```

Avec une Factory :

``` python
strategy = StrategyFactory.create(
    "cleaning",
    "csv"
)
```

La Factory s'occupe de savoir quelle classe doit être instanciée.

------------------------------------------------------------------------

## Exemple conceptuel

``` text
          StrategyFactory
                 │
        ┌────────┴────────┐
        │                 │
      "csv"          "markdown"
        │                 │
        ▼                 ▼
CsvCleaningStrategy   MarkdownCleaningStrategy
```

------------------------------------------------------------------------

# 6. Registry Pattern

## Définition

Le **Registry Pattern** est un catalogue qui associe un nom ou une clé à
une implémentation.

La question à laquelle il répond est :

> **"Quelles implémentations sont disponibles et où puis-je les trouver
> ?"**

Exemple très simple :

``` python
registry = {
    "csv": CsvCleaningStrategy,
    "markdown": MarkdownCleaningStrategy,
}
```

On peut ensuite faire :

``` python
strategy_class = registry["csv"]
```

On obtient :

``` python
CsvCleaningStrategy
```

Puis :

``` python
strategy = strategy_class()
```

On obtient :

``` text
CsvCleaningStrategy()
```

------------------------------------------------------------------------

# 7. Registry dans notre projet

Notre projet possède plusieurs catégories de Strategies.

On peut avoir un Registry conceptuellement organisé comme ceci :

``` text
StrategyRegistry
│
├── loading
│   ├── csv       → CsvLoadingStrategy
│   └── markdown  → MarkdownLoadingStrategy
│
├── cleaning
│   ├── csv       → CsvCleaningStrategy
│   └── markdown  → MarkdownCleaningStrategy
│
├── validation
│   ├── csv       → CsvValidationStrategy
│   └── markdown  → MarkdownValidationStrategy
│
├── derive
│   ├── csv       → CsvDeriveStrategy
│   └── markdown  → MarkdownDeriveStrategy
│
└── save
    ├── csv       → CsvSaveStrategy
    └── markdown  → MarkdownSaveStrategy
```

On peut enregistrer :

``` python
registry.register(
    "cleaning",
    "csv",
    CsvCleaningStrategy,
)
```

et :

``` python
registry.register(
    "cleaning",
    "markdown",
    MarkdownCleaningStrategy,
)
```

Puis récupérer :

``` python
registry.get(
    "cleaning",
    "csv"
)
```

qui retourne :

``` python
CsvCleaningStrategy
```

------------------------------------------------------------------------

# 8. Factory + Registry

Factory et Registry peuvent travailler ensemble.

Le Registry connaît les implémentations disponibles :

``` text
Registry
   │
   ├── ("cleaning", "csv")
   │       → CsvCleaningStrategy
   │
   └── ("cleaning", "markdown")
           → MarkdownCleaningStrategy
```

La Factory utilise ensuite le Registry pour créer l'objet :

``` text
Factory
   │
   ▼
Registry
   │
   ▼
Strategy Class
   │
   ▼
Strategy Instance
```

Par exemple :

``` python
strategy_class = registry.get(
    "cleaning",
    "csv",
)

strategy = strategy_class()
```

Donc :

> **Registry = catalogue**
>
> **Factory = création**

------------------------------------------------------------------------

# 9. Différence entre les quatre Patterns

Voici la distinction la plus importante à retenir.

  -----------------------------------------------------------------------
  Pattern                 Question                Rôle
  ----------------------- ----------------------- -----------------------
  Pipeline                **Dans quel ordre ?**   Organise les étapes

  Strategy                **Comment ?**           Définit une manière de
                                                  réaliser une opération

  Factory                 **Quel objet créer ?**  Crée les objets
                                                  appropriés

  Registry                **Quelles               Catalogue et retrouve
                          implémentations         les implémentations
                          existent ?**            
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 10. Exemple avec une voiture

Pour rendre la différence encore plus intuitive, imaginons une voiture.

## Pipeline

Le trajet suit :

``` text
Start
 ↓
Accelerate
 ↓
Drive
 ↓
Brake
 ↓
Stop
```

Le Pipeline organise l'ordre.

------------------------------------------------------------------------

## Strategy

Pour avancer, on peut avoir différentes stratégies :

``` text
DrivingStrategy
    ├── NormalDriving
    ├── EcoDriving
    └── SportDriving
```

La Strategy détermine **comment** conduire.

------------------------------------------------------------------------

## Factory

La Factory décide quel objet créer :

``` text
"eco"
   ↓
EcoDrivingStrategy()
```

------------------------------------------------------------------------

## Registry

Le Registry contient les possibilités :

``` python
{
    "normal": NormalDrivingStrategy,
    "eco": EcoDrivingStrategy,
    "sport": SportDrivingStrategy,
}
```

------------------------------------------------------------------------

# 11. Application complète à notre projet

Notre architecture peut être comprise ainsi :

``` text
                    INPUT
                      │
                      ▼
              ┌───────────────┐
              │ Type Detection│
              └───────┬───────┘
                      │
             CSV or Markdown
                      │
                      ▼
              ┌───────────────┐
              │    Factory    │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │   Registry    │
              └───────┬───────┘
                      │
          Find appropriate strategies
                      │
                      ▼
                 PIPELINE
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
     Load           Clean         Validate
       │              │              │
       ▼              ▼              ▼
    Strategy       Strategy       Strategy
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                    Derive
                      │
                   Strategy
                      │
                      ▼
                    Save
                      │
                   Strategy
                      │
                      ▼
                    OUTPUT
```

------------------------------------------------------------------------

# 12. Phrase à mémoriser

Une très bonne manière de retenir les quatre concepts est :

> **Pipeline organise.**
>
> **Strategy implémente.**
>
> **Factory construit.**
>
> **Registry enregistre et retrouve.**

Ou encore :

``` text
Pipeline  → ORDER
Strategy  → HOW
Factory   → CREATE
Registry  → LOOKUP
```

------------------------------------------------------------------------

# 13. Attention à ne pas sur-architecturer

Il ne faut pas utiliser un Design Pattern uniquement parce qu'il existe.

Chaque pattern doit résoudre un vrai problème.

Dans notre projet :

### Pipeline

Très utile car nous avons plusieurs étapes :

``` text
Load → Clean → Validate → Derive → Save
```

### Strategy

Très utile car CSV et Markdown nécessitent des traitements différents.

### Factory

Utile pour centraliser la création des Strategies.

### Registry

Utile lorsque le nombre d'implémentations augmente et qu'on veut les
retrouver dynamiquement.

Par exemple, plus tard nous pourrons avoir :

``` text
ChunkingStrategy
    ├── FixedSizeChunking
    ├── RecursiveChunking
    └── MarkdownChunking

EmbeddingStrategy
    ├── SentenceTransformer
    ├── BGE
    └── E5
```

À ce moment-là, un Registry devient particulièrement intéressant.

------------------------------------------------------------------------

# 14. Relation avec la suite du projet RAG

Notre architecture va progressivement évoluer vers :

``` text
Markdown
   ↓
Load
   ↓
Clean
   ↓
Validate
   ↓
Derive
   ↓
Document Objects
   ↓
Chunking
   ↓
Embedding Model Evaluation
   ↓
Choose Model
   ↓
Generate Embeddings
   ↓
Qdrant
```

Les mêmes idées pourront être réutilisées.

Par exemple :

``` text
ChunkingStrategy
      │
      ├── FixedSizeChunking
      ├── RecursiveChunking
      └── SemanticChunking
```

Puis :

``` text
EmbeddingStrategy
      │
      ├── Model A
      ├── Model B
      └── Model C
```

On pourra utiliser une Factory et éventuellement un Registry pour gérer
ces différentes implementations.

------------------------------------------------------------------------

# 15. Résumé final

``` text
┌─────────────────────────────────────────────────────┐
│                     PIPELINE                        │
│                                                     │
│   Load → Clean → Validate → Derive → Save          │
│                                                     │
│   "Dans quel ordre ?"                               │
└─────────────────────────────────────────────────────┘

                         │
                         ▼

┌─────────────────────────────────────────────────────┐
│                    STRATEGY                         │
│                                                     │
│   CSV → CsvCleaningStrategy                         │
│   MD  → MarkdownCleaningStrategy                    │
│                                                     │
│   "Comment ?"                                       │
└─────────────────────────────────────────────────────┘

                         │
                         ▼

┌─────────────────────────────────────────────────────┐
│                     FACTORY                         │
│                                                     │
│   Choisit et construit la bonne Strategy            │
│                                                     │
│   "Quel objet créer ?"                              │
└─────────────────────────────────────────────────────┘

                         │
                         ▼

┌─────────────────────────────────────────────────────┐
│                    REGISTRY                         │
│                                                     │
│   "cleaning" + "csv" → CsvCleaningStrategy          │
│   "cleaning" + "md"  → MarkdownCleaningStrategy     │
│                                                     │
│   "Quelles implémentations sont disponibles ?"      │
└─────────────────────────────────────────────────────┘
```

## À retenir

**Pipeline** → organise les étapes.

**Strategy** → fournit différentes façons de réaliser une étape.

**Factory** → crée la bonne implémentation.

**Registry** → catalogue et retrouve les implémentations.

Ces quatre concepts sont complémentaires, mais ils ne sont pas
obligatoirement utilisés ensemble. On les ajoute lorsque le problème du
projet le justifie.
