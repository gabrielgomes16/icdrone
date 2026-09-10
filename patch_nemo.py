"""
Fixes bugs in the `pytorch-nemo` package (pinned commit in requirements.txt) that
break treinamento.py on modern PyTorch (>=1.13). Run this once, right after
`pip install -r requirements.txt`, from inside the target environment:

    python patch_nemo.py

Safe to run more than once (skips any fix that's already applied). Also safe if the
installed nemo already differs slightly (e.g. a different fallback variant of the
same commit) since bug 1's fix replaces the whole surrounding block by anchor rather
than matching one exact original string.

Bug 1 (graph.py): DeployGraph.__init__ calls torch.onnx.utils._model_to_graph()
with kwargs (`propagate=`, `_retain_param_name=`) that were removed from PyTorch's
internal API in newer versions, or with a positional dummy_input that newer PyTorch
wants wrapped in a tuple. Different installs of the very same pinned commit have
been observed with different fallback variants here (likely because upstream's
setup adapts to the torch version present at install time). Fix: replace the whole
try/except cascade with one that tries every known variant in order, so whichever
one PyTorch actually accepts succeeds.

Bugs 2 and 3 (quant/pact.py): pact_integer_requantize() and
pact_integer_requantize_add() default to D=1 (a plain Python int), but then call
D.clone().detach(...) unconditionally, assuming D is always a torch.Tensor. This
crashes with AttributeError: 'int' object has no attribute 'clone' whenever a
module's D was never explicitly set to a tensor. Fix: convert D to a tensor first
when it isn't one already.

Bug 4 (utils.py): export_onnx() rounds every parameter before exporting
(`param[:] = torch.round(param)`), which can make two different layers' biases
come out bit-identical (e.g. both rounding to zero). torch.onnx.export() is then
called with do_constant_folding=True, which deduplicates identical constant
initializers by replacing one with an `Identity` node pointing at the other.
DORY's ONNX parser doesn't support `Identity` and fails with
"AssertionError: Identity not supported by DORY". Fix: export with
do_constant_folding=False so every parameter keeps its own independent
initializer, identical values or not.

Bug 5 (utils.py): export_onnx() doesn't pin an ONNX opset, so it uses whatever
PyTorch's current default is (opset 14+ on torch 1.13.1). DORY's parser (written
against opset ~9 exports) breaks on newer-opset constructs even after bug 4's
fix and after cleaning up dynamic-shape scaffolding with onnxsim --skip-optimization
and renaming node outputs to sequential integers: e.g. opset 11+ represents Pad's
padding amounts as a runtime input tensor instead of a `pads` attribute, and
DORY_node objects for such Pad nodes never get a `.pads` list, so DORY's own
Pad-merging pattern rewriter crashes with
"AttributeError: 'DORY_node' object has no attribute 'pads'". Fix: export with
opset_version=9, matching the opset DORY's own working reference example
(dory_examples/examples/Nemo_examples/8-bits-2D/dronet_complete/model_int.onnx)
uses, so Conv/Pad go back to the older, attribute-based representation.
"""
import os
import re

import nemo

nemo_dir = os.path.dirname(nemo.__file__)
graph_py = os.path.join(nemo_dir, "graph.py")
pact_py = os.path.join(nemo_dir, "quant", "pact.py")
utils_py = os.path.join(nemo_dir, "utils.py")


def apply_regex_patch(path, pattern, new_block, label):
    with open(path, "r") as f:
        content = f.read()

    if new_block.strip() in content:
        print(f"[{label}] Already up to date.")
        return

    match = pattern.search(content)
    if not match:
        print(f"[{label}] WARNING: expected anchor not found, skipping (nemo version may differ too much for this patch).")
        return

    content = content[: match.start()] + new_block + content[match.end() :]
    with open(path, "w") as f:
        f.write(content)
    print(f"[{label}] Patched.")


# --- Bug 1: graph.py ---
# Replace everything from "with scope_name_workaround(module):" up to (but not
# including) the following "input_dict = {}" line, regardless of which fallback
# variant is currently there.
graph_pattern = re.compile(
    r"[ \t]*with scope_name_workaround\(module\):\n(?:.*\n)*?(?=[ \t]*input_dict = \{\})"
)
graph_new_block = (
    "            with scope_name_workaround(module):\n"
    "                try:\n"
    "                    graph, _params_dict, _torch_out = torch.onnx.utils._model_to_graph(module, dummy_input, propagate=True, _retain_param_name=True)\n"
    "                except TypeError:\n"
    "                    try:\n"
    "                        graph, _params_dict, _torch_out = torch.onnx.utils._model_to_graph(module, dummy_input, _retain_param_name=True)\n"
    "                    except TypeError:\n"
    "                        try:\n"
    "                            graph, _params_dict, _torch_out = torch.onnx.utils._model_to_graph(module, dummy_input)\n"
    "                        except TypeError:\n"
    "                            graph, _params_dict, _torch_out = torch.onnx.utils._model_to_graph(module, (dummy_input,))\n"
)
apply_regex_patch(graph_py, graph_pattern, graph_new_block, "graph.py")

# --- Bugs 2 and 3: quant/pact.py ---
pact_requantize_pattern = re.compile(
    r"def pact_integer_requantize\(t, eps_in, eps_out, D=1\):\n[ \t]*D = D\.clone\(\)\.detach\(\)\.to\(eps_in\.device\)(?: if torch\.is_tensor\(D\) else torch\.tensor\(D, dtype=eps_in\.dtype, device=eps_in\.device\))?\n"
)
pact_requantize_new = (
    "def pact_integer_requantize(t, eps_in, eps_out, D=1):\n"
    "    D = D.clone().detach().to(eps_in.device) if torch.is_tensor(D) else torch.tensor(D, dtype=eps_in.dtype, device=eps_in.device)\n"
)
apply_regex_patch(pact_py, pact_requantize_pattern, pact_requantize_new, "quant/pact.py (pact_integer_requantize)")

pact_requantize_add_pattern = re.compile(
    r"def pact_integer_requantize_add\(\*t, eps_in_list, eps_out, D=1\):\n[ \t]*D = D\.clone\(\)\.detach\(\)\.to\(eps_out\.device\)(?: if torch\.is_tensor\(D\) else torch\.tensor\(D, dtype=eps_out\.dtype, device=eps_out\.device\))?\n"
)
pact_requantize_add_new = (
    "def pact_integer_requantize_add(*t, eps_in_list, eps_out, D=1):\n"
    "    D = D.clone().detach().to(eps_out.device) if torch.is_tensor(D) else torch.tensor(D, dtype=eps_out.dtype, device=eps_out.device)\n"
)
apply_regex_patch(pact_py, pact_requantize_add_pattern, pact_requantize_add_new, "quant/pact.py (pact_integer_requantize_add)")

# --- Bugs 4 and 5: utils.py ---
utils_redefine_pattern = re.compile(
    r"torch\.onnx\.export\(net_inner, dummy_input, file_name, verbose=verbose, do_constant_folding=(?:True|False), input_names=input_names, output_names=output_names, export_params=True(?:, opset_version=9)?\)\n"
)
utils_redefine_new = (
    "torch.onnx.export(net_inner, dummy_input, file_name, verbose=verbose, do_constant_folding=False, input_names=input_names, output_names=output_names, export_params=True, opset_version=9)\n"
)
apply_regex_patch(utils_py, utils_redefine_pattern, utils_redefine_new, "utils.py (export_onnx, redefine_names=True)")

utils_plain_pattern = re.compile(
    r"torch\.onnx\.export\(net_inner, dummy_input, file_name, verbose=verbose, do_constant_folding=(?:True|False), export_params=True(?:, opset_version=9)?\)\n"
)
utils_plain_new = (
    "torch.onnx.export(net_inner, dummy_input, file_name, verbose=verbose, do_constant_folding=False, export_params=True, opset_version=9)\n"
)
apply_regex_patch(utils_py, utils_plain_pattern, utils_plain_new, "utils.py (export_onnx, redefine_names=False)")
