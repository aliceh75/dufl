**dufl** is a dotfile manager with a simplified git-like workflow. It allows you to keep together in a single git repository files that are otherwise spread out across your filesystem. This is typically usefull for tracking configuration files (often known as dotfiles).

**Still under development. Not all features described here are implemented! Wait for 0.1 release plz :)**

Features:
- Leaves your dotfiles intact (no moving & symlinking);
- Simplified git-like workflow;
- Tolerant to users manipulating the git repository directly;
- Detects when elevated privileges are needed, and invokes `sudo` as needed. No confusion about who the current user is;
- Security checks (attempts to detect private ssh keys, etc. and prevents uploading them);
- Home folder aware - so files added from a user's home folder are always checked back out to the home folder, even if the user names are different at the time of adding and checking out.

Anti-Features:
- Developed in Python, so won't be useful in environments where you can't install Python and Python packages.

h2. Example

```sh
    # Create a ~/.dufl folder linked to the given repository,
    # where versions of dotfiles will be stored.
    dufl init http://github.com/example_user/dotfiles.git

    # Add a file to the git repository, and commit it with
    # the given commit message
    dufl add ~/.vimrc -m "Add my vimrc"

    # Push the repository
    dufl push

    # ... edit ~/.vimrc ...

    # See if we have changed any files
    dufl status

    # Note that until we add it again, the changes to ~/.vimrc
    # do *not* get pushed to the git repository. The following
    # does nothing:
    dufl push

    # We need to add it again. This ensures we don't push changes
    # by mistake!
    dufl add ~/.vimrc -m "Use soft tabs"
    dufl push
```

h2. Workflow

The main **dufl** workflow comprises the following commands:

| Command                     | action |
|-----------------------------|--------|
| `dufl init`                 | Initialize your local dufl folder, associated with remote git repository. |
| `dufl add <file name>`      | Add and commit a file to your repository (but don't push) |
| `dufl push`                 | Push local commits to remote repository |
| `dufl fetch`                | Fetch remote commits (but do not deploy them) |
| `dufl checkout <file name>` | Checkout the given file from your fetched dufl repository to your local file system |

In addition, the following commands are available:

| Command                 | action |
|-------------------------|--------|
| `dufl status`           | Show general status (files which have changed, etc.) |
| `dufl diff <file name>` | Show changes in a particular file |

Commands are detailed in the `Commands` section.

**dufl** is home folder aware, which means:

- Files that live under the current user's home folder when added are always checked back out within the current user's home folder, even if the user names are different at the time of adding and checking out;
- Files that do not live under the current user's home folder when added are stored with absolute path, and always checked out at the same absolute location.

h2. Using dufl with sudo

It is best **not to use sudo with dufl**. Because **dufl** is home folder aware, it needs to know who the current user is. When you use `sudo`, the current user changes - and so any operations are done *as the new user* (typically, `root`). There are ways by which **dufl** could check who the original user is (for example by using tools such as `logname`), however this would prevent users from using **dufl** as a different user if that is what they wish to do.

**dufl** will detect when it doesn't have write permission to a file you are checking out, and will at that point invoke `sudo` itself to ask for elevated privileges.

**FEATURE NOT YET IMPLEMENTED**

<a name="keeping_track_of_deployed_filed"></a>
h2. Keeping track of deployed files

**dufl** does not keep track of which version of the file you have deployed to your file system. Being build this way means **dufl** is tolerant to changes you do on the git repository directly. If you want to do some advanced operation not handled by the **dufl** cli, you can do those manually using git - it will not bother **dufl**.

The downside is that **dufl** cannot reliably tell whether you will be overwritting local changes or not when checking out a file. **dufl** will check the local modification time of the file you're checking out, and look at how the file was in the repository at that time. If it cannot be found or if there are changes, **dufl** will warn you you may be overwriting local changes. This approach is not fail proof - git commit timestamps have a granularity of one second, but the same file can be modified and commited multiple times within the same second, so **dufl** might end up looking at the wrong file version.

h2. Commands

h3. dufl init

Creates a local dufl folder (by default `~/.dufl`) and link it to the given git repository. If the given repository already contains files, then they are pulled. If not **dufl** initializes the folder with empty directories and a settings file with default values for your environment.

Example:
```
    dufl init http://github.com/example_user/dotfiles.git
```

If the repository doesn't yet exist upstream, you will get an error from git - but that's fine, you can continue using dufl and create the repository later (before your first push!)

h3. dufl add

`dufl add` adds and commits a file.

Following the git workflow, dufl does not automatically commit modifications to your files. You must explicetly add a file for it to be managed by dufl, and for every change you make to the file you must add it again. This ensures you always know what it being sent to the git repository - important if it is a public one.

Example:
```
    dufl add ~/.vimrc -m "Use soft tabs"
```

The commit message is optional, and defaults to "Update.".

This will prevent you from adding files whose name matches a certain pattern, or who contain certain patterns. For example:

```
    dufl add ~/.ssh/id_rsa
```

Outputs:

```
    This file will not be added because it looks like a private key.
```

Patterns are defined in the config file, see the section `config`.

h3. dufl push

Push all commited changes to the upstream git repository.

Example:
```
    dufl push
```

h3. dufl fetch

**NOT IMPLEMENTED**

Fetch the latest version of the files from the remote repository. This **does not** update your files, you need to run `dufl checout my-file` to get the copy of a given file. However it will update the version against which diffs are shown.

Example:

```
    dufl fetch
```

h3. dufl checkout

**NOT IMPLEMENTED**

Checkouts a file from your dufl repository (as it was when you last ran `dufl fetch`) and installs it locally.

Example:

```
dufl checkout ~/.vimrc
```

Note that the file name is the name you wish to checkout - even if the file doesn't yet exist.

**Warning: this might overwrite local changes!** **dufl** does it's best to check if you have done local modifications to your files, but it is not 100% safe, so extra care must be taken. See [Keeping track of deployed files](#keeping_track_of_deployed_files) for more information on **dufl**'s approach.


h3. dufl status

**NOT IMPLEMENTED**

Shows:
- Files that have modifications (against the file as it was when you last ran `dufl fetch`);
- Commits that have not yet been fetched;
- Commits that have not yet been pushed.

Example:
```
    dufl status
```

h3. dufl diff

**NOT IMPLEMENTED**
Shows the changes made to a particular file. The changes are shown against the file as it was when you last ran `dufl fetch`. If this is a shared repository, and you want to make sure you are diffing against the last version, run `dufl fetch` first.

Example:
```
    dufl diff ~/.vimrc
```

h2. Advanced operations

Unless you've instructed **dufl** otherwise, the git repository is located under `~/.dufl`. Feel free to go there and manipulate the repository directly for more advanced operations, it will not trouble **dufl**.

h2. Settings

When you run `dufl init` this will create a settings in (by default) `~/.dufl/settings.yaml`. The file is a [YAML](http://yaml.org/) formatted file, which looks like:

```yaml
git: /usr/bin/git
suspicious_names: {id_rsa$: this looks like a private key}
suspicous_content: {-BEGIN .+ PRIVATE KEY-: this looks like a private key}
```

Where:

* `git` is the path to your git executable;
* `suspicious_names` is a dictionary associating python regular expression to error message. If any filename matches the regular expression, it will not be added when running `dufl add` and the corresponding message will be output;
* `suspicious_content` is a dictionary associating python regular expression to error message. If any file content matches the regular expression, it will not be added when running `dufl add` and the corresponding message will be output.

h2. Installation

```sh
    git clone https://github.com/aliceh75/dufl.git
    cd dufl
    pip install -r requirements.txt
    pip install .
```

h2. Testing

Make sure you install development requirements:

```sh
    pip install -r dev_requirements.txt
```

And run `py.test`:

```sh
    py.test dufl/tests
```
