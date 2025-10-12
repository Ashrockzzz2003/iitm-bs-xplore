# IITM BS Xplore - Parsing Logic Diagrams

This document contains Mermaid diagrams that explain the parsing logic and data flow in the IITM BS Xplore knowledge graph extraction system.

## 1. Main Parsing Flow Architecture

```mermaid
graph TD
    A[Input Sources] --> B{Input Type Detection}
    B -->|URL| C[URL Processor]
    B -->|File| D[File Processor]
    B -->|Multiple URLs| E[Multi-Source Processor]
    
    C --> F[Fetch HTML from URL]
    F --> G[Detect Parser Type]
    G --> H{Parser Type}
    
    H -->|academics| I[Academics Parser]
    H -->|course| J[Course Parser]
    H -->|generic| K[Generic Parser]
    
    I --> L[Extract Course URLs]
    L --> M[Parse All Course Pages]
    M --> N[Merge Course Graphs]
    
    J --> O[Single Course Graph]
    K --> P[Document Structure Graph]
    
    D --> Q[Read Local Files]
    Q --> R[Apply Specific Parser]
    
    E --> S[Process Each URL]
    S --> T[Create Unified Hierarchy]
    
    N --> U[Knowledge Graph]
    O --> U
    P --> U
    R --> U
    T --> U
    
    U --> V[Add Metadata]
    V --> W[Write Output]
    W --> X[Upload to Neo4j]
```

## 2. Parser Detection and Routing

```mermaid
flowchart TD
    A[URL Input] --> B[Parse URL Components]
    B --> C{Check Domain}
    C -->|study.iitm.ac.in| D{Check Path}
    C -->|Other| E[Generic Parser]
    
    D -->|/ds/academics.html| F[Academics Parser]
    D -->|/es/academics.html| F
    D -->|/ds/course_pages/*.html| G[Course Parser]
    D -->|/es/course_pages/*.html| G
    D -->|Other IITM paths| E
    
    F --> H[Parse Program Structure]
    H --> I[Extract Course URLs]
    I --> J[Parse Each Course]
    J --> K[Merge All Graphs]
    
    G --> L[Parse Single Course]
    L --> M[Extract Course Details]
    
    E --> N[Build Document Outline]
    N --> O[Extract Sections]
    O --> P[Create Generic Graph]
```

## 3. Academics Parsing Logic

```mermaid
graph TD
    A[Academics HTML] --> B[Parse with BeautifulSoup]
    B --> C[Build Document Outline]
    C --> D[Find Target Sections]
    
    D --> E[Fuzzy Match Sections]
    E --> F[Program Structure]
    E --> G[Term Structure]
    E --> H[Course Structure]
    E --> I[Assessments]
    E --> J[Fee Structure]
    E --> K[Rules & Policies]
    
    F --> L[Extract Section Content]
    G --> L
    H --> L
    I --> L
    J --> L
    K --> L
    
    L --> M[Parse Bullets]
    L --> N[Parse Paragraphs]
    L --> O[Parse Labeled Fields]
    L --> P[Extract Tables]
    
    M --> Q[Create Section Nodes]
    N --> Q
    O --> Q
    P --> Q
    
    Q --> R[Classify Academic Levels]
    R --> S[Foundation Level]
    R --> T[Diploma Level]
    R --> U[Degree Level]
    
    S --> V[Extract Course Links]
    T --> V
    U --> V
    
    V --> W[Course ID Detection]
    W --> X[Guess from Text]
    W --> Y[Guess from Href]
    
    X --> Z[Create Course Collections]
    Y --> Z
    
    Z --> AA[Build Knowledge Graph]
    AA --> BB[Return Graph with Metadata]
```

## 4. Course Parsing Logic

```mermaid
graph TD
    A[Course HTML] --> B[Parse with BeautifulSoup]
    B --> C[Extract Course Title]
    C --> D[Guess Course ID]
    
    D --> E[Extract Brief Details]
    E --> F[Parse Course Metadata]
    F --> G[Course Code]
    F --> H[Credits]
    F --> I[Course Type]
    F --> J[Prerequisites]
    F --> K[Duration]
    F --> L[Evaluation Method]
    
    G --> M[Find Field Sections]
    H --> M
    I --> M
    J --> M
    K --> M
    L --> M
    
    M --> N[Fuzzy Match Fields]
    N --> O[Title/Description]
    N --> P[Prerequisites]
    N --> Q[Learning Outcomes]
    N --> R[Assessment Details]
    N --> S[Instructor Info]
    
    O --> T[Extract Content]
    P --> T
    Q --> T
    R --> T
    S --> T
    
    T --> U[Parse Bullets]
    T --> V[Parse Paragraphs]
    T --> W[Parse Labeled Fields]
    
    U --> X[Extract Table Data]
    V --> X
    W --> X
    
    X --> Y[Create Course Node]
    Y --> Z[Extract Prerequisites]
    Z --> AA[Create Prerequisite Edges]
    
    AA --> BB[Return Course Graph]
```

## 5. Generic HTML Parsing Logic

```mermaid
graph TD
    A[Generic HTML] --> B[Parse with BeautifulSoup]
    B --> C[Build Document Outline]
    C --> D[Identify Heading Hierarchy]
    
    D --> E[Filter Valid Headings]
    E --> F[Create Section Tree]
    F --> G[Register Outline Nodes]
    
    G --> H[Extract Section Content]
    H --> I[Next Sibling Content]
    I --> J[Extract Tables]
    J --> K[Attach to Sections]
    
    K --> L[Create Document Root]
    L --> M[Create Section Nodes]
    M --> N[Create Hierarchical Edges]
    
    N --> O[Build Outline Summary]
    O --> P[Return Generic Graph]
```

## 6. Data Flow and Knowledge Graph Construction

```mermaid
graph TD
    A[Raw HTML Input] --> B[HTML Parsing]
    B --> C[Content Extraction]
    
    C --> D[Text Normalization]
    C --> E[Structure Analysis]
    C --> F[Metadata Extraction]
    
    D --> G[Node Creation]
    E --> G
    F --> G
    
    G --> H[Node Types]
    H --> I[Program Nodes]
    H --> J[Section Nodes]
    H --> K[Course Nodes]
    H --> L[Level Nodes]
    H --> M[Collection Nodes]
    
    I --> N[Edge Creation]
    J --> N
    K --> N
    L --> N
    M --> N
    
    N --> O[Edge Types]
    O --> P[HAS_SECTION]
    O --> Q[HAS_LEVEL]
    O --> R[HAS_COURSES]
    O --> S[REQUIRES]
    O --> T[HAS]
    
    P --> U[Graph Assembly]
    Q --> U
    R --> U
    S --> U
    T --> U
    
    U --> V[Metadata Addition]
    V --> W[Parser Information]
    V --> X[Processing Stats]
    V --> Y[Outline Summary]
    
    W --> Z[Final Knowledge Graph]
    X --> Z
    Y --> Z
    
    Z --> AA[Output Formats]
    AA --> BB[JSON Output]
    AA --> CC[Neo4j Upload]
```

## 7. Course URL Extraction Process

```mermaid
graph TD
    A[Academics HTML] --> B[Parse with BeautifulSoup]
    B --> C[Iterate All Elements]
    
    C --> D{Element Type}
    D -->|Heading| E[Update Level Context]
    D -->|Link| F[Extract Link Info]
    D -->|Data URL| G[Extract Data URL]
    
    E --> H[Classify Heading Level]
    H --> I[Foundation/Diploma/Degree]
    I --> J[Update Current Level]
    
    F --> K[Extract Label & Href]
    K --> L[Guess Course ID]
    L --> M{Valid Course ID?}
    M -->|Yes| N[Check for Duplicates]
    M -->|No| O[Skip Link]
    
    G --> P[Extract Data URL]
    P --> Q[Guess Course ID from URL]
    Q --> R{Valid Course ID?}
    R -->|Yes| S[Check for Duplicates]
    R -->|No| T[Skip Data URL]
    
    N --> U[Add to Course List]
    S --> U
    
    U --> V[Convert to Absolute URL]
    V --> W[Add Level Information]
    W --> X[Return Course URLs]
    
    O --> Y[Continue Processing]
    T --> Y
    X --> Y
```

## 8. Multi-Source Processing Flow

```mermaid
graph TD
    A[Multiple Data Sources] --> B[Process Each Source]
    B --> C[Detect Program Type]
    
    C --> D{Program Type}
    D -->|/ds/| E[Data Science Program]
    D -->|/es/| F[Electronics Systems Program]
    D -->|Other| G[Skip Unknown]
    
    E --> H[Process DS Academics]
    F --> I[Process ES Academics]
    
    H --> J[Extract DS Courses]
    I --> K[Extract ES Courses]
    
    J --> L[Parse DS Course Pages]
    K --> M[Parse ES Course Pages]
    
    L --> N[Create DS Program Graph]
    M --> O[Create ES Program Graph]
    
    N --> P[Unified Program Hierarchy]
    O --> P
    
    P --> Q[Create Program Nodes]
    Q --> R[Create Level Hierarchy]
    R --> S[Link Courses to Levels]
    S --> T[Create Cross-Program Edges]
    
    T --> U[Unified Knowledge Graph]
    U --> V[Add Program Metadata]
    V --> W[Return Final Graph]
```

## Key Components Explained

### Parser Types
- **Academics Parser**: Handles program structure pages with course listings
- **Course Parser**: Processes individual course detail pages
- **Generic Parser**: Handles any other HTML documents with outline structure

### Node Types
- **Program**: Root program nodes (IITM BS Degree Program)
- **Level**: Academic levels (Foundation, Diploma, Degree)
- **Section**: Document sections with content
- **Course**: Individual course nodes with metadata
- **Collection**: Lists of courses or other items

### Edge Types
- **HAS_SECTION**: Hierarchical section relationships
- **HAS_LEVEL**: Program to level relationships
- **HAS_COURSES**: Level to course collections
- **REQUIRES**: Course prerequisite relationships
- **HAS**: General containment relationships

### Key Features
- **Fuzzy Matching**: Uses rapidfuzz for flexible section matching
- **Course ID Detection**: Multiple strategies for extracting course identifiers
- **Hierarchical Structure**: Maintains document and academic hierarchies
- **Metadata Preservation**: Tracks parsing statistics and source information
- **Error Handling**: Graceful handling of parsing failures
