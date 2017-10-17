

library(bnlearn)
data("learning.test")
bn.gs <- gs(learning.test)

bn.hc <- hc(learning.test, score='aic')

par(mfrow = c(1,2))
plot(bn.gs, main='Grow-shrink algorithm')
plot(bn.hc, main ='Hill Climbing')

par(mfrow = c(1,2))
highlight.opts <- list(nodes=c('A','B'), arcs = c('A','B'), col='red',fill='grey')
graphviz.plot(bn.gs, main='gs',highlight = highlight.opts)
graphviz.plot(bn.hc, main='hc', highlight = highlight.opts)
