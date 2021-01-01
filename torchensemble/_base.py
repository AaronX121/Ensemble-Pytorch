import abc
import torch
import torch.nn as nn


class BaseModule(abc.ABC, nn.Module):
    """Base class for ensemble methods.

    WARNING: This class cannot be used directly.
    Use the derived classes instead.
    """
    def __init__(self,
                 estimator,
                 n_estimators,
                 estimator_args=None,
                 cuda=True,
                 n_jobs=None,
                 verbose=1):
        super(BaseModule, self).__init__()

        self.base_estimator_ = estimator
        self.n_estimators = n_estimators
        self.estimator_args = estimator_args
        self.device = torch.device("cuda" if cuda else "cpu")
        self.n_jobs = n_jobs
        self.verbose = verbose

        self.estimators_ = nn.ModuleList()

    def __len__(self):
        """Return the number of base estimators in the ensemble."""
        return len(self.estimators_)

    def __getitem__(self, index):
        """Return the index-th base estimator in the ensemble."""
        return self.estimators_[index]

    def _decide_n_outputs(self, train_loader, is_classification=True):
        """Determine the number of outputs according to the train_loader."""
        n_outputs = 0
        # For Classification: n_outputs = n_classes
        if is_classification:
            if hasattr(train_loader.dataset, "classes"):
                n_outputs = len(train_loader.dataset.classes)
            # Infer from the dataloader
            else:
                labels = []
                for _, (_, target) in enumerate(train_loader):
                    labels.append(target)
                labels = torch.unique(torch.cat(labels))
                n_outputs = labels.size()[0]
        # For Regression: n_outputs = n_target_dimensions
        else:
            for _, (_, target) in enumerate(train_loader):
                if len(target.size()) == 1:
                    n_outputs = 1
                else:
                    n_outputs = target.size()[1]
                break
        return n_outputs

    def _make_estimator(self):
        """Make and configure a copy of the `base_estimator_`."""
        if self.estimator_args is None:
            estimator = self.base_estimator_()
        else:
            estimator = self.base_estimator_(**self.estimator_args)
        return estimator.to(self.device)

    def _validate_parameters(self, lr, weight_decay, epochs, log_interval):
        """Validate hyper-parameters on training the ensemble."""

        if not lr > 0:
            msg = ("The learning rate of optimizer = {} should be strictly"
                   " positive.")
            raise ValueError(msg.format(lr))

        if not weight_decay >= 0:
            msg = "The weight decay of optimizer = {} should not be negative."
            raise ValueError(msg.format(weight_decay))

        if not epochs > 0:
            msg = ("The number of training epochs = {} should be strictly"
                   " positive.")
            raise ValueError(msg.format(epochs))

        if not log_interval > 0:
            msg = ("The number of batches to wait before printting the"
                   " training status should be strictly positive, but got {}"
                   " instead.")
            raise ValueError(msg.format(log_interval))

    @abc.abstractmethod
    def forward(self, X):
        """
        Implementation on the data forwarding in the ensemble. Notice
        that the input ``X`` should be a data batch instead of a standalone
        data loader that contains many data batches.
        """

    @abc.abstractmethod
    def fit(self,
            train_loader,
            lr=1e-3,
            weight_decay=5e-4,
            epochs=100,
            optimizer="Adam",
            log_interval=100,
            test_loader=None,
            save_model=True,
            save_dir=None):
        """
        Implementation on the training stage of the ensemble.
        """

    @abc.abstractmethod
    def predict(self, test_loader):
        """
        Implementation on the evaluating stage of the ensemble.
        """
