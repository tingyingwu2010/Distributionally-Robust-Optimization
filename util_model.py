import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from art.classifiers import PyTorchClassifier
from util_MNIST import retrieveMNISTTrainingData, retrieveMNISTTestData, displayImage

img_rows, img_cols = 28, 28

class SimpleNeuralNet(nn.Module):
    """
    Simple neural network consisting of one hidden layer for MNIST.
    This neural network is used as a toy example. 
    """

    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 2, 4)
        self.fc1 = nn.Linear(2 * 25 * 25, 10)

    def forward(self, x):
        output = F.relu(self.conv1(x))
        output = output.view(-1, self.num_flat_features(output))
        output = self.fc1(output)
        return F.softmax(output, dim=1)

    def num_flat_features(self, x):
        size = x.size()[1:]
        num_features = 1
        for s in size:
            num_features *= s
        return num_features

class MNISTClassifier(nn.Module):
    """
    Convolutional neural network used in the tutorial for CleverHans.
    This neural network is also used in experiments by Staib et al. (2017) and
    Sinha et al. (2018).
    """

    def __init__(self, nb_filters=64, activation='relu'):
        super().__init__()
        self.activation = activation
        self.conv1 = nn.Conv2d(1, nb_filters, kernel_size=(8, 8), stride=(2, 2), padding=(3, 3))
        self.conv2 = nn.Conv2d(nb_filters, nb_filters * 2, kernel_size=(6, 6), stride=(2, 2))
        self.conv3 = nn.Conv2d(nb_filters * 2, nb_filters * 2, kernel_size=(5, 5), stride=(1, 1))
        self.fc1 = nn.Linear(nb_filters * 2, 10)

    def forward(self, x):
        outputs = self.conv1(x)
        outputs = self.applyActivation(outputs)
        outputs = self.conv2(outputs)
        outputs = self.applyActivation(outputs)
        outputs = self.conv3(outputs)
        outputs = self.applyActivation(outputs)
        outputs = outputs.view((-1, self.num_flat_features(outputs)))
        outputs = self.fc1(outputs)
        return F.softmax(outputs, dim=1)

    def applyActivation(self, x):
        if self.activation == 'relu':
            return F.relu(x)
        elif self.activation == 'elu':
            return F.elu(x)
        else:
            raise ValueError("The activation function is not valid.")

    def num_flat_features(self, x):
        size = x.size()[1:]
        num_features = 1
        for s in size:
            num_features *= s
        return num_features

def wrapModel(model, loss_criterion):
    """
    Wrap a PyTorch model in the frametwork of ART (Adversarial Robustness
    Toolbox) by IBM.
    """

    optimizer = optim.Adam(model.parameters())
    input_shape = (1, img_rows, img_cols)
    return PyTorchClassifier((0,1), model, loss_criterion, optimizer, input_shape, nb_classes=10)

def trainModel(model, loss_criterion, optimizer, epochs=25, filepath=None):
    # USe GPU for computation if it is available. 
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device) # Load the neural network on GPU if it is available
    print("The neural network is now loaded on {}.".format(device))

    running_loss = 0.0
    train_loader = retrieveMNISTTrainingData(batch_size=128)
    for epoch in range(epochs):
        for i, data in enumerate(train_loader, 0):
            inputs, labels = data
            # Load images and labels on a device
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = loss_criterion(outputs, labels)
            loss.backward()
            running_loss += loss.item()
            optimizer.step()
            if i%20 == 19: 
                print("Epoch: {}, iteration: {}, loss: {}".format(epoch, i, running_loss / 100))
                running_loss = 0.0
    print("Training is complete.")
    if filepath is not None:
        torch.save(model.state_dict(), filepath)
        print("The model is now saved.")

def loadModel(model, filepath):
    """
    Load the set of parameters into the given model.

    Arguments:
        model: a model whose paramters are to be loaded
        filepath: path to the .pt file that stores the parameters to be loaded
    """

    model.load_state_dict(torch.load(filepath))
    "The model is now loaded."
    return model

def evaluateModel(model):
    test_loader = retrieveMNISTTestData()
    correct = 0
    total = 0
    with torch.no_grad():
        for data in test_loader:
            images, labels = data
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    print("The accuracy of this model is {}.".format(correct/total))

if __name__ == "__main__":
    epochs = 25
    loss_criterion = nn.CrossEntropyLoss()

    model_elu = MNISTClassifier(activation='elu')
    optimizer_elu = optim.Adam(model_elu.parameters())

    model_relu = MNISTClassifier(activation='relu')
    optimizer_relu = optim.Adam(model_relu.parameters())

    # The file paths are only valid in UNIX systems. 
    trainModel(model_elu, loss_criterion, optimizer_elu, epochs=epochs, filepath='./models/MNISTClassifier_elu.pt')
    trainModel(model_relu, loss_criterion, optimizer_relu, epochs=epochs, filepath='./models/MNISTClassifier_relu.pt')

    """
    model = SimpleNeuralNet()
    optimizer = optim.Adam(model.parameters())
    trainModel(model, loss_criterion, optimizer, epochs=1, filepath=".\\models\\SimpleModel.pt")
    evaluateModel(model)
    """
