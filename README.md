# AMD-v2 [OAEI 2022](http://disi.unitn.it/~pavel/om2022/papers/oaei22_paper3.pdf)
AgreementMakerDeep (AMD) is a new flexible and extensible ontology matching system with PLM and KGE techniques. In OAEI 2022, we only apply zero-shot learning in [Bio-ML track](https://www.cs.ox.ac.uk/isg/projects/ConCur/oaei/index.html). AMD achieved competetive performance in terms of the evaluateion metrics used in the track without extra training. We also upload our alignments results of all dataset in Bio-ML track for reference.


# Genenral Instructions:

1. Python >= 3.7:

We recommend you to use Anaconda to create a conda environment:
	conda create -n AMD-Seals python=3.7

	conda activate AMD-Seals

2. Other requirements:

	pip install -r requirements.txt
  
Note: This file is able to produce alignments without MELT package.
  
# If you need to attend OAEI and use MELT toolkit, here is more instructions:

1. To evaluate it with previous seals client and MELT Track repository:
	
	java -jar seals-omt-client.jar AMD-seals -x http://oaei.webdatacommons.org/tdrs/ Suite-ID Version-ID /Users/AMD -a

	examples:
	java -jar /Users/Ellen/Downloads/seals-omt-client.jar /Users/Ellen/Desktop/AMDSeals/target/AMD-seals -x http://oaei.webdatacommons.org/tdrs/ largebio largebio-snomed_nci_small_2016 /Users/Ellen/Downloads/AMD -a

2. Re-usage

    If any changes to the model, then use [MELT](http://oaei.ontologymatching.org/2021/melt/index.html) to wrapped and evalute.

For the whole AMD-seals, please refer to [AMD](https://github.com/ellenzhuwang/AgreementMakerDeep) for OAEI 2021.

# Citation

   If you find this repo useful and use our code for your work, please consider citing:
```
@article{wangagreementmakerdeep,
  title={AgreementMakerDeep Results for OAEI2021},
  author={Wang, Zhu and Cruz, Isabel F}
  year={2021}
}
```
and 
```
@article{wang2022amd,
  title={AMD Results for OAEI 2022},
  author={Wang, Zhu},
  year={2022}
}
```

