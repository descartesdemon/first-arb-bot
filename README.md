# first-arb-bot

WIP crypto arbitrage bot

At time of writing bot creates a graph for traversal using Bellman-Ford algorithm to detect arbitrage opportunities.

The main idea behind triangular arbitrage is that if you have currencies $A, B, C, \ldots $ exchanging for rates $r_{AB}, r_{BC}, r_{C\ldots}, r_{\ldots A}$, there is an opportunity for arbitrage when $r_{AB} * r_{BC} * r_{C\ldots} * \ldots * r_{\ldots A} > 1$ (ignoring fees etc.). To make this work with Bellman-Ford, we can detect an arbitrage opportunity as a negative cycle in a currency exchange graph and can use algebra to turn the above condition of arbitrage into a negative cycle.

$$\begin{gather*}
r_{AB} * r_{BC} * r_{CA} > 1\\
\log(r_{AB}) + \log(r_{BC}) + \log(r_{CA}) > 0\\
-\log(r_{AB}) - \log(r_{BC}) - \log(r_{CA}) < 0\\
\end{gather*}$$
