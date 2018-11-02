# bob-slack-interface
Slack bot to communicate with Bob with Bioagents system. You can chat with Bob to work on biological problems by:

- Asking about causal relationships between molecular entities
- Asking about gene alterations, common upstreams, cellular locations
- Asking about drugs, transcription factors, miRNAs and their targets
- Building a mechanistic model and asking about its dynamical properties 



Here are some example sentences to say:


    What is the path between BRAF and MAPK1?    
    What pathways affect BRAF?
    What genes activate ILK?
    How does KRAS activate MAPK3?
    How does BRAF affect MAPK1?
    What genes does MAPK1 phosphorylate?

    What is the drug response on cells with TP53 alterations?
    What is the mutation frequency of TP53 in ovarian serous cystadenocarcinoma?


    What is the most likely cellular location of AKT1 and BRAF?
    What are the common upstreams of AKT1 and BRAF?
    Are there common upstreams of AKT1 and BRAF?
    What genes are mutually exclusive with CDH1 for breast cancer?
    What are the mutually exclusive genes with TP53 for breast cancer?
    What is the mutation significance of TP53 for lung cancer?
    What is the mutation significance of TP53 in ovarian serous cystadenocarcinoma?
    
    Let's build a model.
    MEK phosphorylates ERK.
    EGF binds EGFR.
    EGFR bound to EGF binds GRB2.
    Phosphorylated ERK is active.
    MAP2K1 phosphorylated at S220 phosphoryates MAPK1.
    Active TP53 transcribes MDM2.
    Undo
    Reset    
    Is phosphorylated MAPK1 always high?
    Is the amount of phosphorylated MAPK1 eventually high?
    Is the MAP2K1-MAPK1 complex formed?
    Is the amount of FOS ever high if we increase the amount of ELK1 by 10 fold?
    Does Vemurafenib decrease phosphorylated ERK in the model?
    Does Selumetinib decrease JUN in the model?
    How does KRAS regulate MAP2K1?
    How does HRAS activate MAPK3?
    Does phosphorylation at S222 activate MAP2K1?
    What drugs inhibit MAP2K1?
    Are there any drugs for BRAF?
    Does Vemurafenib inhibit BRAF?
    What are the targets of PLX-4720?
    Which transcription factors regulate frizzled8?
    Does TP53 target MDM2?
    What are the regulators of SRF?
    What transcription factors are shared by SRF, HRAS, and ELK1?
    Which pathways involve TAP1 and JAK1?
    What genes are in the prolactin signaling pathway?