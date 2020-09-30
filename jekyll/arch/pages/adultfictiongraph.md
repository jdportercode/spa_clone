---
layout: vis
title: Reader Network
display_site_title: true
display_page_title: true
hidden: true
order: 3
permalink: /adultfictiongraph/
vis_include: vis/goodreads_genre_nokids_anonymous_tsne_graph.html
---

This Bokeh visualization is based on a different use of t-SNE than our basic map of readers and genre preferences.  Here, the similarity or difference between two readers' tastes is calculated according to the specific books they have read rather than just the genres of the books.  In fact, our genre categories are left out of the algorithm entirely. The code here generates a distance matrix by treating all the books and all the users as part of a bimodal network -- that is, a network with two kinds of nodes that only connect to nodes of the other type. It then "imagines" a process: suppose you talk to a random user and ask for a recommendation. They randomly pick one of the books they've reviewed. Then you talk to other random users until you find one who has also reviewed that book, and ask them for a new recommendation ... ad infinitum. The probability of going from a given user to another in this scenario is the "distance" between them (actually, it's 1 - p instead of p). 

To make things work nicely we posit that all the users have reviewed one amazingly popular book that we don't know the title of. This ensures all users are at least slightly connected in the network. You might say that this imaginary book is goodreads.com.

In this visualization readers appear somewhat less segregated by primary genre preference.  Based on exploration of specific user cases, we believe this is mainly because books that Goodreads users have tended to place on different genre shelves are often more similar to each other than to many of the books with which they share a common shelf.  Some "fantasy" novels, for example, are difficult to distinguish from science fiction while others are difficult to distinguish from romance. A reader whose primary genre is fantasy might therefore be visualized as a blue point very close to many green points (fantasy romance), while another fantasy reader appears as a blue point surrounded by black (science fiction fantasy).    

Scott Enderle, who wrote the code for this t-SNE projection, has called it a map of "browsing distances."  Here is a post where he describes a similar use case: http://www.lagado.name/blog/deriving-browsing-similarity-3/
