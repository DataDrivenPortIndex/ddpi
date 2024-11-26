# Country & City Enrichment

## Overview

The **Country & City Enrichment** component of the **DDPI** (Data-Driven Port Index) system enhances the dataset by associating ports with their corresponding countries and cities. This is achieved by utilizing a list of global country polygons and a list of major cities around the world. Ports are enriched with geographical context, allowing for better analysis and understanding of maritime operations. This enrichment process provides a clearer link between ports and their geographical locations, contributing to more insightful analysis.

---

## Process

### 1. **Country Assignment**: 

The **Country Assignment** process involves mapping each port to its respective country by checking whether the port's geographic location (polygon) lies within the polygon of a specific country. The key steps include:
- **Country Polygon Dataset**: A global list of polygons representing the boundaries of each country is used.
- **Port Polygon Matching**: For each port, the polygon of the port is checked against the polygons of each country.
- **Country Assignment**: If the port polygon lies within the country polygon, the corresponding country is assigned to the port.

### 2. **City Assignment**: 

The **City Assignment** process involves assigning nearby cities to each port based on their proximity. The key steps include:
- **City List**: A dataset of major cities around the world is used. Each city is represented by a geographical coordinate (latitude and longitude).
- **Port Polygon and City Proximity**: The system generates five random points within the polygon of the port and calculates the distance from each point to all cities in the city list.
- **Distance Calculation**: The system calculates the distance from each of the five points to all possible cities and identifies the 10 cities with the smallest distance.
- **City Assignment**: If the distance between a city and a port is below a predefined threshold, the city is assigned to the port. This process is repeated for all ports in the dataset.




