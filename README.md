![ddpi logo](static/images/FullLogo.jpg)

# ddpi

## Overview
This project aims to create a comprehensive, data-driven database of international ports, based on AIS (Automatic Information System) data from global shipping. AIS data, transmitted via radio receivers, provides detailed movement information of ships worldwide, generating several gigabytes of data daily. The goal is to leverage this data to detect and map port locations, identify port boundaries, and eventually extract additional port-related properties.

![ais headmap](static/images/ais_heatmap_dark.png)

## Approach
 - AIS Data Analysis: Identify behavioral patterns in ship movements to detect ports.
 - Clustering Algorithm: Apply clustering techniques to group AIS events into port clusters.
 - Port Properties Extraction: Derive additional details like port boundaries (polygons) and names from the clustered data.


This project lays the foundation for a detailed and accurate port database that can be further expanded with more granular port attributes.